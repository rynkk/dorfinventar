from backend import app

if __name__ == '__main__':
    app.run(debug=True) # For working reloader
    # app.run(debug=True, use_reloader=False)  # For working logging
    #app.run() # Production
