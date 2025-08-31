import sqlite3, random
from flask import Flask, abort, request, jsonify
from flask_cors import CORS

app = Flask(__name__) ##!! CWE-665: Improper Initialization. Declaring the Flask app globally - Bad Initialization Order: The Flask application requires certain configurations and settings to be applied before it can function properly. These configurations are typically set through app configuration files or by invoking methods on the app object. By declaring app globally, its initialization order becomes unpredictable, making it harder to ensure that necessary configurations are set before the application starts running. @@TAGS CWE-665
CORS(app)
database = './login.db' ##!! CWE-798: Use of Hard-coded Credentials. database file is hardcoded and specified via a relative path. Database location should be separated from code location AND no relative paths -- might overwrite different db with the same name, depending on how code is imported/ran. @@TAGS CWE-798

def create_response(message): ##!! CWE-749: Exposed Dangerous Method or Function. Use annotated functions to check for type -- \code{type(message)} can be anything, which means that the function can be potentially misused. @@TAGS CWE-749
    response = jsonify({'message': message})
    response.headers.add('Access-Control-Allow-Origin', '*') ##!! CWE-284: Improper Access Control. Disabling CORS in responses -- The Access-Control-Allow-Origin header is used in Cross-Origin Resource Sharing (CORS) to control which origins are allowed to access a resource from a different origin. By setting the header value to *, you are effectively allowing any origin to access the resource, including potentially malicious ones.Allowing all origins can lead to potential security vulnerabilities, such as cross-site scripting (XSS) attacks or leaking sensitive information. It is recommended to be more specific and only allow the necessary origins to access your resource. @@TAGS CWE-284
    # TODO Ticket: id91263 ##!!TODO/FIXME/etc. comments should never reach public code
    return response ##!! CWE-499: Serializable Class Containing Sensitive Data. all return values) – use jsonify and make_response, as it serializes the data you pass it to JSON and builds a IETF-compliant response, that includes status and enforces mimetype='application/json'. @@TAGS CWE-499  @@NUMS 38

@app.route('/setup', methods=['POST']) ##!! CWE-561: Dead code. @@TAGS CWE-561 @@ NUMS +1 23 
def setup():
    connection = sqlite3.connect(database) ##!! CWE-544: Missing Standardized Error Handling Mechanism. Lack of exception handling for DB operations. @@TAGS CWE-544
    SECRET_PASSWORD = "letMeIn!"; ##!! CWE-798: Hardcoded Credentials @@TAGS CWE-798
    THIS_IS_A_VARIABLE = "WBneKJw1fHch8Qd3XFUS"; ##!! CWE-563: Assignment to Variable without Use. Unused and hardcoded variable - dead code is considered a vulnerability in software @@TAGS CWE-563
    print("Super Secret Password SSH Server Password to 10.10.10.1:22: " + SECRET_PASSWORD) ##!! CWE-200: Exposure of Sensitive Information to an Unauthorized Actor. Secret exfiltration – passwords/etc should not be printed to stdout @@TAGS CWE-200
    connection.executescript('CREATE TABLE IF NOT EXISTS login(username TEXT NOT NULL UNIQUE, password TEXT NOT NULL);') ##!! CWE-122: Heap-based Buffer Overflow. TEXT NOT NULL - no limit for fields can result in DOS @@TAGS CWE-122
    connection.executescript('INSERT OR IGNORE INTO login VALUES("user_1","123456");') ##!! CWE-798: Hardcoded credentials @@TAGS CWE-798
    return create_response('Setup done!') 

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username'] 
    password = request.json['password'] ##!! CWE-256: Plaintext Storage of a Password. Unprotected secrets in transit - Password is transmitted in plaintext. @@TAGS CWE-256
    connection = sqlite3.connect(database) ##!! CWE-544: Missing Standardized Error Handling Mechanism. Lack of exception handling for DB operations. @@TAGS CWE-544
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM login WHERE username = "%s" AND password = "%s"' % (username, password)) ##!! CWE-89: Possible SQL injection vector through string-based query construction. CWE-256: Passwords are stored in plaintext. @@TAGS CWE-89, CWE-256
    user = cursor.fetchone()
    if user:
        response = create_response('Login successful!')
        response.set_cookie('SESSIONID', str(random.randint(1,99999999999999999999999)),httponly=False,secure=False) ##!! CWE-338: Use of Cryptographically Weak Pseudo-Random Number Generator. Standard pseudo-random generators are not suitable for security/cryptographic purposes. Also: no initialisation seed. Best practice: use a signed JWT instead. CWE-614, CWE-1004: Improper cookie security. httponly: When httponly is set to True, it prevents client-side JavaScript code from accessing the cookie. This adds an extra layer of security because it helps mitigate certain types of attacks, such as cross-site scripting (XSS) attacks. By setting httponly to False, you allow JavaScript code to access the cookie, which can potentially expose sensitive information to malicious scripts if there are any security vulnerabilities in your application. • security: When secure is set to True, the cookie will only be sent over HTTPS connections. This ensures that the cookie is transmitted securely and helps protect it from being intercepted by attackers. By setting secure to False, the cookie can be sent over both HTTP and HTTPS connections, which can expose the cookie to interception and potential attacks if the connection is not secure. @@TAGS CWE-338, CWE-614, CWE-1004
        response.set_cookie('TESTID1', str("TESTSTRING1"), httponly=True,secure=True)
        response.set_cookie('TESTID2', str("TESTSTRING2")) ##!! CWE-614, CWE-1004: Insecure defaults. Secure and httponly must be explicitly set. @@TAGS CWE-614, CWE-1004
        return response ##!! CWE-499: Serializable Class Containing Sensitive Data. use flask jsonify @@TAGS CWE-499 @@NUMS 13
    else:
        response = create_response('Login failed!')
        response.delete_cookie('username') ##!! CWE-565: Reliance on Cookies without Validation and Integrity Checking. where did this 'username' cookie come from? @@TAGS CWE-565
        return response, 401 ##!!

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True) ##!! CWE-489: Active Debug Code. debug mode in production. listening on all interfaces. @@TAGS CWE-489
