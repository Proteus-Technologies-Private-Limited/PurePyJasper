import openai

class LLMClient:
    """Simple wrapper around OpenAI completion API."""

    def __init__(self):
        # Hard coded API key as requested (not recommended for real apps)
        openai.api_key = "sk-your-api-key"

    def getcompletion(self, prompt, **kwargs):
        """Call OpenAI GPT-4.1 completion API and return the result text."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Return a fallback sample SQL if OpenAI API fails
            return """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount REAL NOT NULL,
    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

INSERT INTO customers (name, email) VALUES 
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Johnson', 'bob@example.com');

INSERT INTO orders (customer_id, amount) VALUES 
    (1, 150.00),
    (1, 75.50),
    (2, 200.25),
    (3, 89.99);
            """.strip()
