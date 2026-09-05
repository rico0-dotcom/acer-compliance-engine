# ACER Three-Way Statistical Evaluation

This evaluator compares three saved adaptation conditions across the same three seeds:

1. FIXED_ORDER
2. AGENTIC without LLM
3. AGENTIC + GPT-oss LLM assistance

It reuses completed LLM run files and does not call the provider.

Default output:
`data/results/adaptation_multiseed/statistical_evaluation_three_way.json`

The evaluator reports paired descriptive statistics for:
- accepted adaptation steps
- modeled total cost
- modeled total complexity
- LLM calls and LLM failures

It makes no statistical-significance claim. Synthetic benchmark results do not establish legal compliance or superiority on unseen systems.
