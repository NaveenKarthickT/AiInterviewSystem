$payload = @{email = "testuser@example.com"; password = "Secret123!"; full_name = "Test User"} | ConvertTo-Json

Invoke-RestMethod `
    -Method POST `
    -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
    -ContentType "application/json" `
    -Body $payload
