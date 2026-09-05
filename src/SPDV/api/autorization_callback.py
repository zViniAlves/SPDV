from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()


@app.get("/callback")
async def shopee_callback(request: Request):
    """
    Endpoint de callback do OAuth da Shopee.
    A Shopee redireciona o navegador para cá após a autorização,
    anexando `code` e `shop_id` (ou `main_account_id`) na query string.
    """
    params = dict(request.query_params)

    code = params.get("code")
    shop_id = params.get("shop_id")

    return {
        "code": code,
        "shop_id": shop_id,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
