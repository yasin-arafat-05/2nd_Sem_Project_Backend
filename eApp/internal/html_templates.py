"""
HTML Email Templates for eApp
"""

def payment_subscription_expired(subscription_expires_at: str, username: str) -> str:
    """HTML template for subscription expiration email"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Expired</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f4f4f4;
            color: #333333;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}

        .container {{
            max-width: 600px;
            width: 100%;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
        }}

        .header {{
            background-color: #ff4444;
            padding: 20px;
            text-align: center;
            color: #ffffff;
        }}

        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }}

        .content {{
            padding: 20px;
            color: #333333;
        }}

        .content h2 {{
            color: #ff4444;
            font-size: 20px;
            margin: 0 0 15px;
        }}

        .details-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        .details-table th, .details-table td {{
            padding: 12px;
            border: 1px solid #dddddd;
            text-align: left;
            font-size: 14px;
        }}

        .details-table th {{
            background-color: #f9f9f9;
            font-weight: bold;
            width: 30%;
        }}

        .details-table td {{
            background-color: #ffffff;
        }}

        .button {{
            display: block;
            width: 200px;
            padding: 12px 0;
            background-color: #ff4444;
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px auto 0;
            text-align: center;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 12px;
            color: #777777;
            background-color: #f9f9f9;
            border-radius: 0 0 8px 8px;
        }}

        @media only screen and (max-width: 600px) {{
            .container {{
                width: 100%;
                border-radius: 0;
            }}

            .header {{
                padding: 15px;
            }}

            .header h1 {{
                font-size: 20px;
            }}

            .content {{
                padding: 15px;
            }}

            .content h2 {{
                font-size: 18px;
            }}

            .details-table th,
            .details-table td {{
                padding: 8px;
                font-size: 12px;
                display: block;
                width: 100%;
                box-sizing: border-box;
            }}

            .details-table th {{
                background-color: #f0f0f0;
                border-bottom: none;
            }}

            .details-table td {{
                border-top: none;
                background-color: #ffffff;
            }}

            .button {{
                width: 90%;
                margin: 20px auto 0;
            }}
        }}
    </style>
</head>
<body>
    <center>
        <div class="container">
            <div class="header">
                <h1>Subscription Expired</h1>
            </div>
            <div class="content">
                <h2>Hello, {username}!</h2>
                <p>Your subscription has expired on <strong>{subscription_expires_at}</strong>.</p>
                <p>Please renew your subscription to continue enjoying our premium features.</p>
                
                <table class="details-table">
                    <tr>
                        <th>Username</th>
                        <td>{username}</td>
                    </tr>
                    <tr>
                        <th>Expiration Date</th>
                        <td>{subscription_expires_at}</td>
                    </tr>
                </table>
                
                <p>We value your continued support and look forward to serving you!</p>
                <a href="https://your-app-domain.com/renew" class="button">Renew Subscription</a>
            </div>
            <div class="footer">
                <p>Thank you for being with us! If you have any questions, contact us at support@galacticart.com.</p>
                <p>&copy; 2025 eApp. All rights reserved.</p>
            </div>
        </div>
    </center>
</body>
</html>
"""

