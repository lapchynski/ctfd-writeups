from CTFd import create_app

app = create_app()

# Debug mode, listening on any hosts
app.run(debug=True, host="0.0.0.0", port=4000)
