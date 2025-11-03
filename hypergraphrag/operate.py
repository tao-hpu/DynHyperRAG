import asyncio
import json
import re
from tqdm.asyncio import tqdm as tqdm_async
from typing import Union
from collections import Counter, defaultdict
import warnings
from .utils import (
    logger,
    clean_str,
    compute_mdhash_id,
    decode_tokens_by_tiktoken,
    encode_string_by_tiktoken,
    is_float_regex,
    list_of_list_to_csv,
    pack_user_ass_to_openai_messages,
    split_string_by_multi_markers,
    truncate_list_by_token_size,
    process_combine_contexts,
    compute_args_hash,
    handle_cache,
    save_to_cache,
    CacheData,
)
from .base import (
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
    TextChunkSchema,
    QueryParam,
)
from .prompt import GRAPH_FIELD_SEP, PROMPTS


def chunking_by_token_size(
    content: str, overlap_token_size=128, max_token_size=1024, tiktoken_model="gpt-4o"
):
    tokens = encode_string_by_tiktoken(content, model_name=tiktoken_model)
    results = []
    for index, start in enumerate(
        range(0, len(tokens), max_token_size - overlap_token_size)
    ):
        chunk_content = decode_tokens_by_tiktoken(
            tokens[start : start + max_token_size], model_name=tiktoken_model
        )
        results.append(
            {
                "tokens": min(max_token_size, len(tokens) - start),
                "content": chunk_content.strip(),
                "chunk_order_index": index,
            }
        )
    return results


async def _handle_entity_relation_summary(
    entity_or_relation_name: str,
    description: str,
    global_config: dict,
) -> str:
    use_llm_func: callable = global_config["llm_model_func"]
    llm_max_tokens = global_config["llm_model_max_token_size"]
    tiktoken_model_name = global_config["tiktoken_model_name"]
    summary_max_tokens = global_config["entity_summary_to_max_tokens"]
    language = global_config["addon_params"].get(
        "language", PROMPTS["DEFAULT_LANGUAGE"]
    )

    tokens = encode_string_by_tiktoken(description, model_name=tiktoken_model_name)
    if len(tokens) < summary_max_tokens:  # No need for summary
        return description
    prompt_template = PROMPTS["summarize_entity_descriptions"]
    use_description = decode_tokens_by_tiktoken(
        tokens[:llm_max_tokens], model_name=tiktoken_model_name
    )
    context_base = dict(
        entity_name=entity_or_relation_name,
        description_list=use_description.split(GRAPH_FIELD_SEP),
        language=language,
    )
    use_prompt = prompt_template.format(**context_base)
    logger.debug(f"Trigger summary: {entity_or_relation_name}")
    summary = await use_llm_func(use_prompt, max_tokens=summary_max_tokens)
    return summary


async def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
    now_hyper_relation: str,
):
    if len(record_attributes) < 5 or record_attributes[0] != '"entity"' or now_hyper_relation == "":
        return None
    # add this record as a node in the G
    entity_name = clean_str(record_attributes[1].upper())
    if not entity_name.strip():
        return None
    entity_type = clean_str(record_attributes[2].upper())
    entity_description = clean_str(record_attributes[3])
    weight = (
        float(record_attributes[-1]) if is_float_regex(record_attributes[-1]) else 50.0
    )
    hyper_relation = now_hyper_relation
    entity_source_id = chunk_key
    return dict(
        entity_name=entity_name,
        entity_type=entity_type,
        description=entity_description,
        weight=weight,
        hyper_relation=hyper_relation,
        source_id=entity_source_id,
    )


async def _handle_single_hyperrelation_extraction(
    record_attributes: list[str],
    chunk_key: str,
):
    if len(record_attributes) < 3 or record_attributes[0] != '"hyper-relation"':
        return None
    # add this record as edge
    knowledge_fragment = clean_str(record_attributes[1])
    edge_source_id = chunk_key
    weight = (
        float(record_attributes[-1]) if is_float_regex(record_attributes[-1]) else 1.0
    )
    return dict(
        hyper_relation="<hyperedge>"+knowledge_fragment,
        weight=weight,
        source_id=edge_source_id,
    )
    

async def _merge_hyperedges_then_upsert(
    hyperedge_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
):
    already_weights = []
    already_source_ids = []

    already_hyperedge = await knowledge_graph_inst.get_node(hyperedge_name)
    if already_hyperedge is not None:
        already_weights.append(already_hyperedge["weight"])
        already_source_ids.extend(
            split_string_by_multi_markers(already_hyperedge["source_id"], [GRAPH_FIELD_SEP])
        )

    weight = sum([dp["weight"] for dp in nodes_data] + already_weights)
    source_id = GRAPH_FIELD_SEP.join(
        set([dp["source_id"] for dp in nodes_data] + already_source_ids)
    )
    node_data = dict(
        role = "hyperedge",
        weight=weight,
        source_id=source_id,
    )
    await knowledge_graph_inst.upsert_node(
        hyperedge_name,
        node_data=node_data,
    )
    node_data["hyperedge_name"] = hyperedge_name
    return node_data


async def _merge_nodes_then_upsert(
    entity_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
):
    already_entity_types = []
    already_source_ids = []
    already_description = []

    already_node = await knowledge_graph_inst.get_node(entity_name)
    if already_node is not None:
        already_entity_types.append(already_node["entity_type"])
        already_source_ids.extend(
            split_string_by_multi_markers(already_node["source_id"], [GRAPH_FIELD_SEP])
        )
        already_description.append(already_node["description"])

    entity_type = sorted(
        Counter(
            [dp["entity_type"] for dp in nodes_data] + already_entity_types
        ).items(),
        key=lambda x: x[1],
        reverse=True,
    )[0][0]
    description = GRAPH_FIELD_SEP.join(
        sorted(set([dp["description"] for dp in nodes_data] + already_description))
    )
    source_id = GRAPH_FIELD_SEP.join(
        set([dp["source_id"] for dp in nodes_data] + already_source_ids)
    )
    description = await _handle_entity_relation_summary(
        entity_name, description, global_config
    )
    node_data = dict(
        role="entity",
        entity_type=entity_type,
        description=description,
        source_id=source_id,
    )
    await knowledge_graph_inst.upsert_node(
        entity_name,
        node_data=node_data,
    )
    node_data["entity_name"] = entity_name
    return node_data


async def _merge_edges_then_upsert(
    entity_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
):
    edge_data = []
    
    for node in nodes_data:
        source_id = node["source_id"]
        hyper_relation = node["hyper_relation"]
        weight = node["weight"]
        
        already_weights = []
        already_source_ids = []
        
        if await knowledge_graph_inst.has_edge(hyper_relation, entity_name):
            already_edge = await knowledge_graph_inst.get_edge(hyper_relation, entity_name)
            already_weights.append(already_edge["weight"])
            already_source_ids.extend(
                split_string_by_multi_markers(already_edge["source_id"], [GRAPH_FIELD_SEP])
            )
        
        weight = sum([weight] + already_weights)
        source_id = GRAPH_FIELD_SEP.join(
            set([source_id] + already_source_ids)
        )

        await knowledge_graph_inst.upsert_edge(
            hyper_relation,
            entity_name,
            edge_data=dict(
                weight=weight,
                source_id=source_id,
            ),
        )

        edge_data.append(dict(
            src_id=hyper_relation,
            tgt_id=entity_name,
            weight=weight,
        ))

    return edge_data


async def extract_entities(
    chunks: dict[str, TextChunkSchema],
    knowledge_graph_inst: BaseGraphStorage,
    entity_vdb: BaseVectorStorage,
    hyperedge_vdb: BaseVectorStorage,
    global_config: dict,
) -> Union[BaseGraphStorage, None]:
    use_llm_func: callable = global_config["llm_model_func"]
    entity_extract_max_gleaning = global_config["entity_extract_max_gleaning"]

    ordered_chunks = list(chunks.items())
    # add language and example number params to prompt
    language = global_config["addon_params"].get(
        "language", PROMPTS["DEFAULT_LANGUAGE"]
    )
    entity_types = global_config["addon_params"].get(
        "entity_types", PROMPTS["DEFAULT_ENTITY_TYPES"]
    )
    example_number = global_config["addon_params"].get("example_number", None)
    if example_number and example_number < len(PROMPTS["entity_extraction_examples"]):
        examples = "\n".join(
            PROMPTS["entity_extraction_examples"][: int(example_number)]
        )
    else:
        examples = "\n".join(PROMPTS["entity_extraction_examples"])

    example_context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        entity_types=",".join(entity_types),
        language=language,
    )
    # add example's format
    examples = examples.format(**example_context_base)

    entity_extract_prompt = PROMPTS["entity_extraction"]
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        # entity_types=",".join(entity_types),
        examples=examples,
        language=language,
    )

    continue_prompt = PROMPTS["entiti_continue_extraction"]
    if_loop_prompt = PROMPTS["entiti_if_loop_extraction"]

    already_processed = 0
    already_entities = 0
    already_relations = 0

    async def _process_single_content(chunk_key_dp: tuple[str, TextChunkSchema]):
        nonlocal already_processed, already_entities, already_relations
        chunk_key = chunk_key_dp[0]
        chunk_dp = chunk_key_dp[1]
        content = chunk_dp["content"]
        # hint_prompt = entity_extract_prompt.format(**context_base, input_text=content)
        hint_prompt = entity_extract_prompt.format(
            **context_base, input_text="{input_text}"
        ).format(**context_base, input_text=content)

        final_result = await use_llm_func(hint_prompt)
        history = pack_user_ass_to_openai_messages(hint_prompt, final_result)
        for now_glean_index in range(entity_extract_max_gleaning):
            glean_result = await use_llm_func(continue_prompt, history_messages=history)

            history += pack_user_ass_to_openai_messages(continue_prompt, glean_result)
            final_result += glean_result
            if now_glean_index == entity_extract_max_gleaning - 1:
                break

            if_loop_result: str = await use_llm_func(
                if_loop_prompt, history_messages=history
            )
            if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
            if if_loop_result != "yes":
                break

        records = split_string_by_multi_markers(
            final_result,
            [context_base["record_delimiter"], context_base["completion_delimiter"]],
        )

        maybe_nodes = defaultdict(list)
        maybe_edges = defaultdict(list)
        now_hyper_relation=""
        for record in records:
            record = re.search(r"\((.*)\)", record)
            if record is None:
                continue
            record = record.group(1)
            record_attributes = split_string_by_multi_markers(
                record, [context_base["tuple_delimiter"]]
            )
            if_relation = await _handle_single_hyperrelation_extraction(
                record_attributes, chunk_key
            )
            if if_relation is not None:
                maybe_edges[if_relation["hyper_relation"]].append(
                    if_relation
                )
                now_hyper_relation = if_relation["hyper_relation"]
                
            if_entities = await _handle_single_entity_extraction(
                record_attributes, chunk_key, now_hyper_relation
            )
            if if_entities is not None:
                maybe_nodes[if_entities["entity_name"]].append(if_entities)
                continue
            
        already_processed += 1
        already_entities += len(maybe_nodes)
        already_relations += len(maybe_edges)
        now_ticks = PROMPTS["process_tickers"][
            already_processed % len(PROMPTS["process_tickers"])
        ]
        print(
            f"{now_ticks} Processed {already_processed} chunks, {already_entities} entities(duplicated), {already_relations} relations(duplicated)\r",
            end="",
            flush=True,
        )
        return dict(maybe_nodes), dict(maybe_edges)

    results = []
    for result in tqdm_async(
        asyncio.as_completed([_process_single_content(c) for c in ordered_chunks]),
        total=len(ordered_chunks),
        desc="Extracting entities from chunks",
        unit="chunk",
    ):
        results.append(await result)

    maybe_nodes = defaultdict(list)
    maybe_edges = defaultdict(list)
    for m_nodes, m_edges in results:
        for k, v in m_nodes.items():
            maybe_nodes[k].extend(v)
        for k, v in m_edges.items():
            maybe_edges[k].extend(v)
            
    logger.info("Inserting hyperedges into storage...")
    all_hyperedges_data = []
    for result in tqdm_async(
        asyncio.as_completed(
            [
                _merge_hyperedges_then_upsert(k, v, knowledge_graph_inst, global_config)
                for k, v in maybe_edges.items()
            ]
        ),
        total=len(maybe_edges),
        desc="Inserting hyperedges",
        unit="entity",
    ):
        all_hyperedges_data.append(await result)
            
    logger.info("Inserting entities into storage...")
    all_entities_data = []
    for result in tqdm_async(
        asyncio.as_completed(
            [
                _merge_nodes_then_upsert(k, v, knowledge_graph_inst, global_config)
                for k, v in maybe_nodes.items()
            ]
        ),
        total=len(maybe_nodes),
        desc="Inserting entities",
        unit="entity",
    ):
        all_entities_data.append(await result)

    logger.info("Inserting relationships into storage...")
    all_relationships_data = []
    for result in tqdm_async(
        asyncio.as_completed(
            [
                _merge_edges_then_upsert(k, v, knowledge_graph_inst, global_config)
                for k, v in maybe_nodes.items()
            ]
        ),
        total=len(maybe_nodes),
        desc="Inserting relationships",
        unit="relationship",
    ):
        all_relationships_data.append(await result)

    if not len(all_hyperedges_data) and not len(all_entities_data) and not len(all_relationships_data):
        logger.warning(
            "Didn't extract any hyperedges and entities, maybe your LLM is not working"
        )
        return None

    if not len(all_hyperedges_data):
        logger.warning("Didn't extract any hyperedges")
    if not len(all_entities_data):
        logger.warning("Didn't extract any entities")
    if not len(all_relationships_data):
        logger.warning("Didn't extract any relationships")

    if hyperedge_vdb is not None:
        data_for_vdb = {
            compute_mdhash_id(dp["hyperedge_name"], prefix="rel-"): {
                "content": dp["hyperedge_name"],
                "hyperedge_name": dp["hyperedge_name"],
            }
            for dp in all_hyperedges_data
        }
        await hyperedge_vdb.upsert(data_for_vdb)

    if entity_vdb is not None:
        data_for_vdb = {
            compute_mdhash_id(dp["entity_name"], prefix="ent-"): {
                "content": dp["entity_name"] + dp["description"],
                "entity_name": dp["entity_name"],
            }
            for dp in all_entities_data
        }
        await entity_vdb.upsert(data_for_vdb)

    return knowledge_graph_inst


async def kg_query(
    query,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    hyperedges_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    query_param: QueryParam,
    global_config: dict,
    hashing_kv: BaseKVStorage = None,
) -> str:
    # Handle cache
    use_model_func = global_config["llm_model_func"]
    args_hash = compute_args_hash(query_param.mode, query)
    cached_response, quantized, min_val, max_val = await handle_cache(
        hashing_kv, args_hash, query, query_param.mode
    )
    if cached_response is not None:
        return cached_response
    
    # Track retrieved hyperedges for dynamic update
    retrieved_hyperedges_for_update = []
    
    language = global_config["addon_params"].get(
        "language", PROMPTS["DEFAULT_LANGUAGE"]
    )
    entity_types = global_config["addon_params"].get(
        "entity_types", PROMPTS["DEFAULT_ENTITY_TYPES"]
    )
    example_number = global_config["addon_params"].get("example_number", None)
    if example_number and example_number < len(PROMPTS["entity_extraction_examples"]):
        examples = "\n".join(
            PROMPTS["entity_extraction_examples"][: int(example_number)]
        )
    else:
        examples = "\n".join(PROMPTS["entity_extraction_examples"])

    example_context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        entity_types=",".join(entity_types),
        language=language,
    )
    # add example's format
    examples = examples.format(**example_context_base)

    entity_extract_prompt = PROMPTS["entity_extraction"]
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        # entity_types=",".join(entity_types),
        examples=examples,
        language=language,
    )
    
    hint_prompt = entity_extract_prompt.format(
        **context_base, input_text="{input_text}"
    ).format(**context_base, input_text=query)

    final_result = await use_model_func(hint_prompt)

    logger.info("kw_prompt result:")
    print(final_result)
    hl_keywords, ll_keywords = [], []
    try:
        records = split_string_by_multi_markers(
            final_result,
            [context_base["record_delimiter"], context_base["completion_delimiter"]],
        )
        for record in records:
            record = re.search(r"\((.*)\)", record)
            if record is None:
                continue
            record = record.group(1)
            record_attributes = split_string_by_multi_markers(
                record, [context_base["tuple_delimiter"]]
            )
            if len(record_attributes) == 3 and record_attributes[0] == '"hyper-relation"':
                hl_keywords.append("<hyperedge>"+clean_str(record_attributes[1]))
            elif len(record_attributes) == 5 and record_attributes[0] == '"entity"':
                ll_keywords.append(clean_str(record_attributes[1]).upper())
            else:
                continue
    # Handle parsing error
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e} {final_result}")
        return PROMPTS["fail_response"]

    # Handdle keywords missing
    if hl_keywords == [] and ll_keywords == []:
        logger.warning("low_level_keywords and high_level_keywords is empty")
        return PROMPTS["fail_response"]
    if ll_keywords == [] and query_param.mode in ["hybrid"]:
        logger.warning("low_level_keywords is empty")
        return PROMPTS["fail_response"]
    else:
        ll_keywords = ", ".join(ll_keywords)
    if hl_keywords == [] and query_param.mode in ["hybrid"]:
        logger.warning("high_level_keywords is empty")
        return PROMPTS["fail_response"]
    else:
        hl_keywords = ", ".join(hl_keywords)

    # Build context with efficient retrieval support
    keywords = [ll_keywords, hl_keywords]
    context, retrieved_hyperedges_for_update = await _build_query_context(
        keywords,
        knowledge_graph_inst,
        entities_vdb,
        hyperedges_vdb,
        text_chunks_db,
        query_param,
        global_config=global_config,
        original_query=query,
    )

    if query_param.only_need_context:
        return context
    if context is None:
        return PROMPTS["fail_response"]
    sys_prompt_temp = PROMPTS["rag_response"]
    sys_prompt = sys_prompt_temp.format(
        context_data=context, response_type=query_param.response_type
    )
    if query_param.only_need_prompt:
        return sys_prompt
    response = await use_model_func(
        query,
        system_prompt=sys_prompt,
        stream=query_param.stream,
    )
    if isinstance(response, str) and len(response) > len(sys_prompt):
        response = (
            response.replace(sys_prompt, "")
            .replace("user", "")
            .replace("model", "")
            .replace(query, "")
            .replace("<system>", "")
            .replace("</system>", "")
            .strip()
        )

    # Save to cache
    await save_to_cache(
        hashing_kv,
        CacheData(
            args_hash=args_hash,
            content=response,
            prompt=query,
            quantized=quantized,
            min_val=min_val,
            max_val=max_val,
            mode=query_param.mode,
        ),
    )
    
    # Dynamic weight update (Task 9.1 & 9.2)
    # Extract feedback and update weights asynchronously (non-blocking)
    # Use asyncio.create_task to run in background
    asyncio.create_task(
        _perform_dynamic_update_async(
            response,
            retrieved_hyperedges_for_update,
            knowledge_graph_inst,
            global_config,
            query
        )
    )
    
    return response


async def _build_query_context(
    query: list,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    hyperedges_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    query_param: QueryParam,
    global_config: dict = None,
    original_query: str = None,
):
    """
    Build query context with optional efficient retrieval.
    
    Args:
        query: List of [low_level_keywords, high_level_keywords]
        knowledge_graph_inst: Graph storage instance
        entities_vdb: Entity vector database
        hyperedges_vdb: Hyperedge vector database
        text_chunks_db: Text chunks database
        query_param: Query parameters
        global_config: Global configuration (optional, for efficient retrieval)
        original_query: Original query string (optional, for entity type identification)
    
    Returns:
        Tuple of (context_str, retrieved_hyperedges)
    """
    # Track retrieved hyperedges for dynamic update
    retrieved_hyperedges = []

    ll_kewwords, hl_keywrds = query[0], query[1]
    if query_param.mode in ["local", "hybrid"]:
        if ll_kewwords == "":
            ll_entities_context, ll_relations_context, ll_text_units_context = (
                "",
                "",
                "",
            )
            warnings.warn(
                "Low Level context is None. Return empty Low entity/relationship/source"
            )
            query_param.mode = "global"
        else:
            (
                ll_entities_context,
                ll_relations_context,
                ll_text_units_context,
                ll_hyperedges,
            ) = await _get_node_data(
                query_keywords=ll_kewwords,
                knowledge_graph_inst=knowledge_graph_inst,
                entities_vdb=entities_vdb,
                text_chunks_db=text_chunks_db,
                query_param=query_param,
                global_config=global_config,
                query=original_query,
            )
            retrieved_hyperedges.extend(ll_hyperedges)
    if query_param.mode in ["global", "hybrid"]:
        if hl_keywrds == "":
            hl_entities_context, hl_relations_context, hl_text_units_context = (
                "",
                "",
                "",
            )
            warnings.warn(
                "High Level context is None. Return empty High entity/relationship/source"
            )
            query_param.mode = "local"
        else:
            (
                hl_entities_context,
                hl_relations_context,
                hl_text_units_context,
                hl_hyperedges,
            ) = await _get_edge_data(
                hl_keywrds,
                knowledge_graph_inst,
                hyperedges_vdb,
                text_chunks_db,
                query_param,
                global_config=global_config,
                query=original_query,
            )
            retrieved_hyperedges.extend(hl_hyperedges)
            if (
                hl_entities_context == ""
                and hl_relations_context == ""
                and hl_text_units_context == ""
            ):
                logger.warn("No high level context found. Switching to local mode.")
                query_param.mode = "local"
    if query_param.mode == "hybrid":
        entities_context, relations_context, text_units_context = combine_contexts(
            [hl_entities_context, ll_entities_context],
            [hl_relations_context, ll_relations_context],
            [hl_text_units_context, ll_text_units_context],
        )
    elif query_param.mode == "local":
        entities_context, relations_context, text_units_context = (
            ll_entities_context,
            ll_relations_context,
            ll_text_units_context,
        )
    elif query_param.mode == "global":
        entities_context, relations_context, text_units_context = (
            hl_entities_context,
            hl_relations_context,
            hl_text_units_context,
        )
    
    context_str = f"""
-----Entities-----
```csv
{entities_context}
```
-----Relationships-----
```csv
{relations_context}
```
-----Sources-----
```csv
{text_units_context}
```
"""
    
    return context_str, retrieved_hyperedges


async def _get_node_data(
    query_keywords,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    query_param: QueryParam,
    global_config: dict = None,
    query: str = None,
):
    """
    Get node (entity) data with optional efficient retrieval integration.
    
    This function now supports quality-aware ranking for related hyperedges.
    
    Args:
        query_keywords: Query keywords for entity search
        knowledge_graph_inst: Graph storage instance
        entities_vdb: Vector database for entities
        text_chunks_db: Text chunks database
        query_param: Query parameters
        global_config: Global configuration (optional, for efficient retrieval)
        query: Original query string (optional, for ranking)
    
    Returns:
        Tuple of (entities_context, relations_context, text_units_context, retrieved_hyperedges)
    """
    # get similar entities
    results = await entities_vdb.query(query_keywords, top_k=query_param.top_k)
    if not len(results):
        return "", "", "", []
    # get entity information
    node_datas = await asyncio.gather(
        *[knowledge_graph_inst.get_node(r["entity_name"]) for r in results]
    )
    if not all([n is not None for n in node_datas]):
        logger.warning("Some nodes are missing, maybe the storage is damaged")

    # get entity degree
    node_degrees = await asyncio.gather(
        *[knowledge_graph_inst.node_degree(r["entity_name"]) for r in results]
    )
    node_datas = [
        {**n, "entity_name": k["entity_name"], "rank": d}
        for k, n, d in zip(results, node_datas, node_degrees)
        if n is not None
    ]
    # get entitytext chunk
    use_text_units = await _find_most_related_text_unit_from_entities(
        node_datas, query_param, text_chunks_db, knowledge_graph_inst
    )
    # get relate edges
    use_relations = await _find_most_related_edges_from_entities(
        node_datas, query_param, knowledge_graph_inst
    )
    
    # Apply quality-aware ranking to related hyperedges if enabled
    if global_config is not None:
        addon_params = global_config.get("addon_params", {})
        retrieval_config = addon_params.get("retrieval_config", {})
        use_efficient_retrieval = retrieval_config.get("entity_filter_enabled", False)
        lite_config = addon_params.get("lite_config", {})
        use_lite_mode = lite_config.get("enabled", False)
        
        if use_efficient_retrieval and not use_lite_mode:
            try:
                from .retrieval import QualityAwareRanker
                
                ranker = QualityAwareRanker(retrieval_config)
                
                logger.info("[Quality Ranker] Applying quality-aware ranking to related hyperedges")
                use_relations = await ranker.rank_hyperedges(
                    query if query else "",
                    use_relations,
                    graph=knowledge_graph_inst
                )
                
            except ImportError as e:
                logger.debug(f"QualityAwareRanker not available: {e}")
            except Exception as e:
                logger.error(f"Quality-aware ranking failed for related edges: {e}")
    logger.info(
        f"Local query uses {len(node_datas)} entites, {len(use_relations)} relations, {len(use_text_units)} text units"
    )

    # build prompt
    entites_section_list = [["id", "entity", "type", "description"]]
    for i, n in enumerate(node_datas):
        entites_section_list.append(
            [
                i,
                n["entity_name"],
                n.get("entity_type", "UNKNOWN"),
                n.get("description", "UNKNOWN"),
            ]
        )
    entities_context = list_of_list_to_csv(entites_section_list)

    relations_section_list = [
        ["id", "hyperedge", "related_entities"]
    ]
    for i, e in enumerate(use_relations):
        relations_section_list.append(
            [
                i,
                e["description"],
                e["related_nodes"]
            ]
        )
    relations_context = list_of_list_to_csv(relations_section_list)

    text_units_section_list = [["id", "content"]]
    for i, t in enumerate(use_text_units):
        text_units_section_list.append([i, t["content"]])
    text_units_context = list_of_list_to_csv(text_units_section_list)
    
    # Prepare hyperedges for dynamic update
    retrieved_hyperedges = [
        {
            "id": e.get("hyperedge_id", e["description"]),
            "hyperedge": e["description"],
            "distance": e.get("rank", 0.5)
        }
        for e in use_relations
    ]
    
    return entities_context, relations_context, text_units_context, retrieved_hyperedges


async def _find_most_related_text_unit_from_entities(
    node_datas: list[dict],
    query_param: QueryParam,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    knowledge_graph_inst: BaseGraphStorage,
):
    text_units = [
        split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
        for dp in node_datas
    ]
    edges = await asyncio.gather(
        *[knowledge_graph_inst.get_node_edges(dp["entity_name"]) for dp in node_datas]
    )
    all_one_hop_nodes = set()
    for this_edges in edges:
        if not this_edges:
            continue
        all_one_hop_nodes.update([e[1] for e in this_edges])

    all_one_hop_nodes = list(all_one_hop_nodes)
    all_one_hop_nodes_data = await asyncio.gather(
        *[knowledge_graph_inst.get_node(e) for e in all_one_hop_nodes]
    )

    # Add null check for node data
    all_one_hop_text_units_lookup = {
        k: set(split_string_by_multi_markers(v["source_id"], [GRAPH_FIELD_SEP]))
        for k, v in zip(all_one_hop_nodes, all_one_hop_nodes_data)
        if v is not None and "source_id" in v  # Add source_id check
    }

    all_text_units_lookup = {}
    for index, (this_text_units, this_edges) in enumerate(zip(text_units, edges)):
        for c_id in this_text_units:
            if c_id not in all_text_units_lookup:
                all_text_units_lookup[c_id] = {
                    "data": await text_chunks_db.get_by_id(c_id),
                    "order": index,
                    "relation_counts": 0,
                }

            if this_edges:
                for e in this_edges:
                    if (
                        e[1] in all_one_hop_text_units_lookup
                        and c_id in all_one_hop_text_units_lookup[e[1]]
                    ):
                        all_text_units_lookup[c_id]["relation_counts"] += 1

    # Filter out None values and ensure data has content
    all_text_units = [
        {"id": k, **v}
        for k, v in all_text_units_lookup.items()
        if v is not None and v.get("data") is not None and "content" in v["data"]
    ]

    if not all_text_units:
        logger.warning("No valid text units found")
        return []

    all_text_units = sorted(
        all_text_units, key=lambda x: (x["order"], -x["relation_counts"])
    )

    all_text_units = truncate_list_by_token_size(
        all_text_units,
        key=lambda x: x["data"]["content"],
        max_token_size=query_param.max_token_for_text_unit,
    )

    all_text_units = [t["data"] for t in all_text_units]
    return all_text_units


async def _find_most_related_edges_from_entities(
    node_datas: list[dict],
    query_param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
):
    all_related_edges = await asyncio.gather(
        *[knowledge_graph_inst.get_node_edges(dp["entity_name"]) for dp in node_datas]
    )
    all_edges = []
    seen = set()

    for this_edges in all_related_edges:
        for e in this_edges:
            sorted_edge = tuple(e)
            if sorted_edge not in seen:
                seen.add(sorted_edge)
                all_edges.append(sorted_edge)

    all_edges_pack = await asyncio.gather(
        *[knowledge_graph_inst.get_edge(e[0], e[1]) for e in all_edges]
    )
    all_edges_degree = await asyncio.gather(
        *[knowledge_graph_inst.edge_degree(e[0], e[1]) for e in all_edges]
    )
    all_edges_data = [
        {"src_tgt": k, "rank": d, "description": k[1], **v}
        for k, v, d in zip(all_edges, all_edges_pack, all_edges_degree)
        if v is not None
    ]
    all_edges_data = sorted(
        all_edges_data, key=lambda x: (x["rank"], x["weight"]), reverse=True
    )
    all_edges_data = truncate_list_by_token_size(
        all_edges_data,
        key=lambda x: x["description"],
        max_token_size=query_param.max_token_for_global_context,
    )
    all_related_nodes = await asyncio.gather(
        *[knowledge_graph_inst.get_node_edges(edge["src_tgt"][1]) for edge in all_edges_data]
    )
    all_nodes = []
    for this_nodes in all_related_nodes:
        all_nodes.append("|".join([n[1] for n in this_nodes]))
    all_edges_data = [
        {**e, "related_nodes": n}
        for e, n in zip(all_edges_data, all_nodes)
    ]
    return all_edges_data


async def _get_edge_data(
    keywords,
    knowledge_graph_inst: BaseGraphStorage,
    hyperedges_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    query_param: QueryParam,
    global_config: dict = None,
    query: str = None,
):
    """
    Get edge (hyperedge) data with optional efficient retrieval integration.
    
    This function now supports:
    - Entity type filtering (Task 10)
    - Quality-aware ranking (Task 11)
    - Lite retriever mode (Task 12)
    
    Args:
        keywords: Query keywords
        knowledge_graph_inst: Graph storage instance
        hyperedges_vdb: Vector database for hyperedges
        text_chunks_db: Text chunks database
        query_param: Query parameters
        global_config: Global configuration (optional, for efficient retrieval)
        query: Original query string (optional, for entity type identification)
    
    Returns:
        Tuple of (entities_context, relations_context, text_units_context, retrieved_hyperedges)
    """
    # Check if efficient retrieval is enabled
    use_efficient_retrieval = False
    use_lite_mode = False
    retrieval_config = {}
    
    if global_config is not None:
        addon_params = global_config.get("addon_params", {})
        retrieval_config = addon_params.get("retrieval_config", {})
        use_efficient_retrieval = retrieval_config.get("entity_filter_enabled", False)
        
        lite_config = addon_params.get("lite_config", {})
        use_lite_mode = lite_config.get("enabled", False)
    
    # Use lite retriever if enabled
    if use_lite_mode and global_config is not None:
        try:
            from .retrieval import LiteRetriever
            
            lite_retriever = LiteRetriever(
                knowledge_graph_inst,
                hyperedges_vdb,
                lite_config
            )
            
            logger.info("[Lite Mode] Using LiteRetriever for efficient retrieval")
            results = await lite_retriever.retrieve(keywords, top_k=query_param.top_k)
            
        except ImportError as e:
            logger.warning(f"Failed to import LiteRetriever: {e}. Falling back to standard retrieval.")
            results = await hyperedges_vdb.query(keywords, top_k=query_param.top_k)
        except Exception as e:
            logger.error(f"LiteRetriever failed: {e}. Falling back to standard retrieval.")
            results = await hyperedges_vdb.query(keywords, top_k=query_param.top_k)
    else:
        # Standard vector retrieval
        results = await hyperedges_vdb.query(keywords, top_k=query_param.top_k)

    if not len(results):
        return "", "", "", []

    # Get hyperedge node data
    edge_datas = await asyncio.gather(
        *[knowledge_graph_inst.get_node(r["hyperedge_name"]) for r in results]
    )

    if not all([n is not None for n in edge_datas]):
        logger.warning("Some edges are missing, maybe the storage is damaged")
    
    # Combine vector results with node data
    edge_datas = [
        {"hyperedge": k["hyperedge_name"], "rank": k["distance"], **v}
        for k, v in zip(results, edge_datas)
        if v is not None
    ]
    
    # Apply entity type filtering if enabled
    if use_efficient_retrieval and query is not None and global_config is not None:
        try:
            from .retrieval import EntityTypeFilter
            
            entity_filter = EntityTypeFilter(
                knowledge_graph_inst,
                retrieval_config,
                llm_model_func=global_config.get("llm_model_func")
            )
            
            # Identify relevant entity types from query
            relevant_types = await entity_filter.identify_relevant_types(query)
            logger.info(f"[Entity Filter] Identified relevant types: {relevant_types}")
            
            # Filter hyperedges by entity type
            hyperedge_ids = [e["hyperedge"] for e in edge_datas]
            filtered_ids = await entity_filter.filter_hyperedges_by_type(
                hyperedge_ids,
                relevant_types
            )
            
            # Keep only filtered hyperedges
            original_count = len(edge_datas)
            edge_datas = [e for e in edge_datas if e["hyperedge"] in filtered_ids]
            filtered_count = len(edge_datas)
            
            logger.info(
                f"[Entity Filter] Filtered {original_count} → {filtered_count} hyperedges "
                f"({(1 - filtered_count/original_count)*100:.1f}% reduction)"
            )
            
            # If too few results after filtering, fall back to unfiltered
            if filtered_count < max(3, query_param.top_k // 2):
                logger.warning(
                    f"[Entity Filter] Too few results after filtering ({filtered_count}). "
                    "Using unfiltered results."
                )
                edge_datas = [
                    {"hyperedge": k["hyperedge_name"], "rank": k["distance"], **v}
                    for k, v in zip(results, edge_datas)
                    if v is not None
                ]
                
        except ImportError as e:
            logger.warning(f"Failed to import EntityTypeFilter: {e}. Skipping entity filtering.")
        except Exception as e:
            logger.error(f"Entity type filtering failed: {e}. Continuing without filtering.")
    
    # Apply quality-aware ranking if enabled and not in lite mode
    if use_efficient_retrieval and not use_lite_mode and global_config is not None:
        try:
            from .retrieval import QualityAwareRanker
            
            ranker = QualityAwareRanker(retrieval_config)
            
            logger.info("[Quality Ranker] Applying quality-aware ranking")
            edge_datas = await ranker.rank_hyperedges(
                query if query else keywords,
                edge_datas,
                graph=knowledge_graph_inst
            )
            
        except ImportError as e:
            logger.warning(f"Failed to import QualityAwareRanker: {e}. Using standard ranking.")
            # Fall back to standard ranking
            edge_datas = sorted(
                edge_datas, key=lambda x: (x["rank"], x["weight"]), reverse=True
            )
        except Exception as e:
            logger.error(f"Quality-aware ranking failed: {e}. Using standard ranking.")
            edge_datas = sorted(
                edge_datas, key=lambda x: (x["rank"], x["weight"]), reverse=True
            )
    else:
        # Standard ranking by similarity and weight
        edge_datas = sorted(
            edge_datas, key=lambda x: (x["rank"], x["weight"]), reverse=True
        )
    
    # Truncate by token size
    edge_datas = truncate_list_by_token_size(
        edge_datas,
        key=lambda x: x["hyperedge"],
        max_token_size=query_param.max_token_for_global_context,
    )
    all_related_nodes = await asyncio.gather(
        *[knowledge_graph_inst.get_node_edges(edge["hyperedge"]) for edge in edge_datas]
    )
    all_nodes = []
    for this_nodes in all_related_nodes:
        all_nodes.append("|".join([n[1] for n in this_nodes]))
    edge_datas = [
        {**e, "related_nodes": n}
        for e, n in zip(edge_datas, all_nodes)
    ]

    use_entities = await _find_most_related_entities_from_relationships(
        edge_datas, query_param, knowledge_graph_inst
    )
    use_text_units = await _find_related_text_unit_from_relationships(
        edge_datas, query_param, text_chunks_db, knowledge_graph_inst
    )
    logger.info(
        f"Global query uses {len(use_entities)} entites, {len(edge_datas)} relations, {len(use_text_units)} text units"
    )

    relations_section_list = [
        ["id", "hyperedge", "related_entities"]
    ]
    for i, e in enumerate(edge_datas):
        relations_section_list.append(
            [
                i,
                e["hyperedge"],
                e['related_nodes']
            ]
        )
    relations_context = list_of_list_to_csv(relations_section_list)

    entites_section_list = [["id", "entity", "type", "description"]]
    for i, n in enumerate(use_entities):
        entites_section_list.append(
            [
                i,
                n["entity_name"],
                n.get("entity_type", "UNKNOWN"),
                n.get("description", "UNKNOWN")
            ]
        )
    entities_context = list_of_list_to_csv(entites_section_list)

    text_units_section_list = [["id", "content"]]
    for i, t in enumerate(use_text_units):
        text_units_section_list.append([i, t["content"]])
    text_units_context = list_of_list_to_csv(text_units_section_list)
    
    # Prepare hyperedges for dynamic update
    retrieved_hyperedges = [
        {
            "id": e["hyperedge"],
            "hyperedge": e["hyperedge"],
            "distance": e.get("rank", 0.5)
        }
        for e in edge_datas
    ]
    
    return entities_context, relations_context, text_units_context, retrieved_hyperedges


async def _find_most_related_entities_from_relationships(
    edge_datas: list[dict],
    query_param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
):
    
    node_datas = await asyncio.gather(
        *[knowledge_graph_inst.get_node_edges(edge["hyperedge"]) for edge in edge_datas]
    )
    
    entity_names = []
    seen = set()

    for node_data in node_datas:
        for e in node_data:
            if e[1] not in seen:
                entity_names.append(e[1])
                seen.add(e[1])

    node_datas = await asyncio.gather(
        *[knowledge_graph_inst.get_node(entity_name) for entity_name in entity_names]
    )

    node_degrees = await asyncio.gather(
        *[knowledge_graph_inst.node_degree(entity_name) for entity_name in entity_names]
    )
    node_datas = [
        {**n, "entity_name": k, "rank": d}
        for k, n, d in zip(entity_names, node_datas, node_degrees)
    ]

    node_datas = truncate_list_by_token_size(
        node_datas,
        key=lambda x: x["description"],
        max_token_size=query_param.max_token_for_local_context,
    )

    return node_datas


async def _find_related_text_unit_from_relationships(
    edge_datas: list[dict],
    query_param: QueryParam,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    knowledge_graph_inst: BaseGraphStorage,
):
    text_units = [
        split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
        for dp in edge_datas
    ]
    all_text_units_lookup = {}

    for index, unit_list in enumerate(text_units):
        for c_id in unit_list:
            if c_id not in all_text_units_lookup:
                chunk_data = await text_chunks_db.get_by_id(c_id)
                # Only store valid data
                if chunk_data is not None and "content" in chunk_data:
                    all_text_units_lookup[c_id] = {
                        "data": chunk_data,
                        "order": index,
                    }

    if not all_text_units_lookup:
        logger.warning("No valid text chunks found")
        return []

    all_text_units = [{"id": k, **v} for k, v in all_text_units_lookup.items()]
    all_text_units = sorted(all_text_units, key=lambda x: x["order"])

    # Ensure all text chunks have content
    valid_text_units = [
        t for t in all_text_units if t["data"] is not None and "content" in t["data"]
    ]

    if not valid_text_units:
        logger.warning("No valid text chunks after filtering")
        return []

    truncated_text_units = truncate_list_by_token_size(
        valid_text_units,
        key=lambda x: x["data"]["content"],
        max_token_size=query_param.max_token_for_text_unit,
    )

    all_text_units: list[TextChunkSchema] = [t["data"] for t in truncated_text_units]

    return all_text_units


def combine_contexts(entities, relationships, sources):
    # Function to extract entities, relationships, and sources from context strings
    hl_entities, ll_entities = entities[0], entities[1]
    hl_relationships, ll_relationships = relationships[0], relationships[1]
    hl_sources, ll_sources = sources[0], sources[1]
    # Combine and deduplicate the entities
    combined_entities = process_combine_contexts(hl_entities, ll_entities)

    # Combine and deduplicate the relationships
    combined_relationships = process_combine_contexts(
        hl_relationships, ll_relationships
    )

    # Combine and deduplicate the sources
    combined_sources = process_combine_contexts(hl_sources, ll_sources)

    return combined_entities, combined_relationships, combined_sources



async def _perform_dynamic_update_async(
    answer: str,
    retrieved_hyperedges: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
    query: str = None
):
    """
    Perform dynamic weight update asynchronously after query completion.
    
    This function runs in the background without blocking the query response.
    It implements Task 9.2: Asynchronous weight update with proper error handling
    and race condition prevention.
    
    Features:
    - Non-blocking execution using asyncio.create_task()
    - Comprehensive error handling
    - Race condition prevention through atomic operations
    - Detailed logging for monitoring
    
    Args:
        answer: Generated answer text
        retrieved_hyperedges: List of retrieved hyperedge dictionaries
        knowledge_graph_inst: Graph storage instance
        global_config: Global configuration dictionary
        query: Original query (optional, for logging)
    """
    # Check if dynamic update is enabled
    dynamic_config = global_config.get("addon_params", {}).get("dynamic_config", {})
    if not dynamic_config.get("enabled", False):
        logger.debug("Dynamic update is disabled, skipping weight update")
        return
    
    if not retrieved_hyperedges:
        logger.debug("No hyperedges retrieved, skipping weight update")
        return
    
    try:
        # Import dynamic modules
        from .dynamic import FeedbackExtractor, WeightUpdater
        
        # Get embedding function
        embedding_func = global_config.get("embedding_func")
        if embedding_func is None:
            logger.warning("Embedding function not available, skipping dynamic update")
            return
        
        # Initialize feedback extractor
        feedback_config = {
            "method": dynamic_config.get("feedback_method", "embedding"),
            "similarity_threshold": dynamic_config.get("feedback_threshold", 0.7),
            "citation_threshold": 0.8,
        }
        feedback_extractor = FeedbackExtractor(embedding_func, feedback_config)
        
        # Initialize weight updater
        weight_config = {
            "strategy": dynamic_config.get("strategy", "ema"),
            "update_alpha": dynamic_config.get("update_alpha", 0.1),
            "decay_factor": dynamic_config.get("decay_factor", 0.99),
        }
        weight_updater = WeightUpdater(knowledge_graph_inst, weight_config)
        
        # Extract feedback signals
        logger.debug(f"[Async] Extracting feedback for {len(retrieved_hyperedges)} hyperedges")
        feedback_signals = await feedback_extractor.extract_feedback(
            answer,
            retrieved_hyperedges,
            metadata={"query": query} if query else None
        )
        
        if not feedback_signals:
            logger.debug("[Async] No feedback signals extracted")
            return
        
        # Update weights with race condition handling
        # The WeightUpdater uses atomic upsert_node operations to prevent race conditions
        logger.info(f"[Async] Updating weights for {len(feedback_signals)} hyperedges")
        update_count = 0
        failed_updates = []
        
        for he_id, feedback in feedback_signals.items():
            try:
                # Each update is atomic at the storage level
                new_weight = await weight_updater.update_weights(
                    he_id,
                    feedback,
                    metadata={"query": query} if query else None
                )
                update_count += 1
                logger.debug(
                    f"[Async] Updated {he_id}: feedback={feedback:.3f}, new_weight={new_weight:.3f}"
                )
            except Exception as e:
                logger.error(f"[Async] Failed to update weight for {he_id}: {e}")
                failed_updates.append(he_id)
        
        # Log summary
        logger.info(
            f"[Async] Dynamic update completed: {update_count}/{len(feedback_signals)} "
            f"hyperedges updated successfully"
        )
        
        if failed_updates:
            logger.warning(
                f"[Async] {len(failed_updates)} updates failed: {failed_updates[:5]}"
                + ("..." if len(failed_updates) > 5 else "")
            )
        
    except ImportError as e:
        logger.error(f"[Async] Failed to import dynamic modules: {e}")
    except Exception as e:
        logger.error(f"[Async] Dynamic update failed: {e}", exc_info=True)
    finally:
        # Ensure cleanup even if errors occur
        logger.debug("[Async] Dynamic update task finished")
