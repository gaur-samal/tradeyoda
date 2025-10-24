# Test script
from dhanhq import DhanContext, dhanhq
from datetime import datetime, timedelta

client_id = "1105816689"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzYxMzYzNDcyLCJpYXQiOjE3NjEyNzcwNzIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1ODE2Njg5In0.JB-K-91j0-aKAnPMiv6VUYqKft9SSm8chOwNEEq-EZ3NKpZPu-jELcyMpb5QGtAWyFO89RbbRRjqAQ7DszQURQ"
dhan_context = DhanContext(client_id,access_token)
dhan = dhanhq(dhan_context)

# Get next Tuesday
now = datetime.now()
days_ahead = 1 - now.weekday()
if days_ahead <= 0:
    days_ahead += 7
next_tuesday = now + timedelta(days=days_ahead)
expiry = next_tuesday.strftime("%Y-%m-%d")

exp_list = dhan.expiry_list(
              under_security_id=13,                       # Nifty
              under_exchange_segment="IDX_I"
           )
print(f"exp_list: {exp_list}")
print(f"Testing with expiry: {expiry}")


result = dhan.option_chain(
    under_security_id=13,
    under_exchange_segment="IDX_I",
    expiry=expiry
)

print(f"Result: {result}")

