import requests
from typing import List, Dict
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv


class bankTransactionAPI:

    def __init__(self):
        load_dotenv()

        self.token = os.getenv("API_TOKEN")
        self.url = "https://yveyrngnwkgcbzilnrls.supabase.co/functions/v1/bank-transactions-import"

        if not self.token:
            raise ValueError("API_TOKEN não encontrado no .env")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def sendTransactions(self, transactions: List[Dict]):

        payload = {
            "transactions": transactions
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                print("✅ Transações enviadas com sucesso")
                return response.json()

            if response.status_code == 400:
                print("❌ Erro de validação")
                print(response.json())
                return

            if response.status_code == 401:
                print("❌ Token ausente")
                return

            if response.status_code == 403:
                print("❌ Token inválido ou inativo")
                return

            if response.status_code == 409:
                print("⚠️ TransactionId já foi processado")
                print(response.json())
                return

            print(f"❌ Erro inesperado: {response.status_code}")
            print(response.text)

        except requests.exceptions.Timeout:
            print("❌ Timeout ao chamar API")

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {str(e)}")

    def buildTransaction(
        self,
        description: str,
        amount: float,
        transactionType: str,
        accountId: str = None,
        invoiceNumber: str = None,
        supplier: str = None
    ) -> Dict:

        if transactionType not in ["debit", "credit"]:
            raise ValueError("Type deve ser 'debit' ou 'credit'")

        if amount <= 0:
            raise ValueError("Amount deve ser maior que 0")

        transaction = {
            "TransactionId": str(uuid.uuid4()),
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Description": description,
            "Amount": round(amount, 2),
            "Type": transactionType
        }

        if accountId:
            transaction["AccountId"] = accountId

        if invoiceNumber:
            transaction["InvoiceNumber"] = invoiceNumber

        if supplier:
            transaction["Supplier"] = supplier

        return transaction

    def execute(self):

        transaction = self.buildTransaction(
            description="Pagamento fornecedor Priortec",
            amount=350.00,
            transactionType="debit",
            supplier="Priortec",
            invoiceNumber="1111"
        )

        self.sendTransactions([transaction])


if __name__ == "__main__":
    api = bankTransactionAPI()
    api.execute()