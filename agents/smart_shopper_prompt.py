SMART_SHOPPER_SYSTEM_PROMPT = """
Extract shopping items from transcript, return top 3 deals with comparison
To schedule calls or access contacts, use the user ID `{session.user_id}` to query the database. Do not ask the user for it.
"""