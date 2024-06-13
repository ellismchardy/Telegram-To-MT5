import re

def parse_signal(message):
    match = re.search(r'(Buy|Sell)[\s\S]*TP:\s*([\d.]+)', message)
    if match:
        action, tp = match.groups()
        tp = float(tp)
        if action == 'Buy':
            tp -= 2
        elif action == 'Sell':
            tp += 2
        print("Action:", action)
        print("Target Price:", tp)
        return action, tp
    return None, None

# Example usage
#message = "🔔 Ready Signal! \n\nBuy Gold @ 2344.940\n\nTP: 2347.000"
message = "🔔 Ready Signal! \n\nSell Gold @ 2344.940\n\nTP: 2347.000"
print("Message:", message)
action, tp = parse_signal(message)
print("Result:", action, tp)
