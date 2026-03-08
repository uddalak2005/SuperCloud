from fastapi import FastAPI
from fixer import Fixer

app = FastAPI()

fixer = Fixer()


@app.post("/fix")
async def fix(payload: dict):

    print("[Fixer] Received remediation request:", payload)

    try:
        result = fixer.handle_incident(payload)
        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        print("[Fixer] Error:", str(e))

        return {
            "status": "failed",
            "error": str(e)
        }