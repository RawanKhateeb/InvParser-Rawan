from mvc_model.myAppView import app
#Ignore This Function
if __name__ == "__main__": # pragma: no cover
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
    