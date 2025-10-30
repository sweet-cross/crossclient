from crossclient.client import CrossClient

if __name__ == "__main__":
    client = CrossClient(
        username="jabmin",
        password="jabmin_password",
        base_url="http://localhost/api/v1",
    )
    resp = client.get("file/")
    print(resp.json())
    print("done")
