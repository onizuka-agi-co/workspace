# Test Cases for Secret Detection

## Case 1: API_KEY with quotes
```bash
API_KEY="sk-proj-AbCdEf1234567890XYZ"
```

## Case 2: api_token without quotes
```python
api_token = AbCdEf1234567890GhIjKl
```

## Case 3: SECRET_KEY with single quotes
```bash
SECRET_KEY='super_secret_key_1234567890abcdef'
```

## Case 4: password assignment
```javascript
const password = "MyP@ssw0rd12345678";
```

## Case 5: auth token in URL format
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
```

## Case 6: credentials object
```json
{
  "credentials": {
    "access_key": "AKIAIOSFODNN7EXAMPLE",
    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }
}
```

## Case 7: Normal content (should pass)
```markdown
This is a normal markdown file.
No secrets here, just regular text.
The quick brown fox jumps over the lazy dog.
```
