def handler(request):
    # No server‑side session in Vercel functions.
    return {
        "statusCode": 200,
        "body": "Logged out"
    }
