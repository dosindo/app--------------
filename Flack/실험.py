from flask import Flask, request, render_template, redirect, url_for

@실험.route('/daum')
def daum():
    return redirect("https://www.daum.net/")

if __name__ == '__main__':
    with app.test_request_context():
        print(url_for('daum'))

    실험.run(debug=True)