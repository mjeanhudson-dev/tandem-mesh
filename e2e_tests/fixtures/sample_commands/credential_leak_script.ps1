# Script containing sensitive credential tokens that must be sanitized by scanner
$apiKey = "sk-ant-api03-abcdef1234567890abcdef1234567890abcdef"
$ghToken = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
$dbPassword = "P@ssw0rd1234!SecretToken"
$bearer = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"

Write-Output "Connecting with token: $apiKey"
