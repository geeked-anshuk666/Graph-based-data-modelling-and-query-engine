def build_answer_messages(question: str, sql: str, rows: list[dict]) -> list[dict]:
    # cap row data to 50 rows in the prompt to avoid token bloat
    display_rows = rows[:50]
    note = ""
    if len(rows) > 50:
        note = f"\n(Showing first 50 of {len(rows)} results)"

    return [
        {
            "role": "system",
            "content": (
                "You are answering questions about SAP Order-to-Cash business data. "
                "Answer in 2-4 sentences based only on the provided query results. "
                "Reference specific IDs, amounts, and counts from the data. "
                "Do not make up data that isn't in the results."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"SQL executed:\n{sql}\n\n"
                f"Results:\n{display_rows}{note}"
            ),
        },
    ]
