import boto3

def populate_database():
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('FAQKnowledgeBase')

faq_data = [
    {
        'keyword': 'precio',
        'respuesta_es': 'Precios desde $50 mensuales',
        'respuesta_en': 'Prices from $50 monthly', 
        'respuesta_pt': 'Preços a partir de $50 mensais'
    }
]

for item in faq_data:
    table.put_item(Item=item)
    print(f"Insertado: {item['keyword']}")

if name == "main":
populate_database()