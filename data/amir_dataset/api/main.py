from fastapi import FastAPI

app = FastAPI()

@app.get("/predict")
def predict(team_a: str, team_b: str):

    # fake example values (later connect to engine)
    xg_a = 1.6
    xg_b = 0.8

    return {
        "team_a": team_a,
        "team_b": team_b,
        "expected_goals": {
            team_a: xg_a,
            team_b: xg_b
        }
    }
