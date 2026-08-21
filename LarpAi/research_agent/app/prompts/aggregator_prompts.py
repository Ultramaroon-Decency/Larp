AGGREGATOR_SYSTEM_PROMPT = (
    "You are an expert Research Aggregator. Your task is to merge, deduplicate, and "
    "normalize structured findings from multi-source research executions. "
    "Identify and remove duplicate claims, resolve conflicting information, "
    "and calculate weighted confidence scores."
)

AGGREGATOR_USER_TEMPLATE = (
    "Aggregate the following research findings into unified structured data:\n"
    "Search Results: {search_results}\n"
    "Claims: {claims}\n"
    "Summaries: {summaries}\n"
    "Citations: {citations}"
)
