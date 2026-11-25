import sounddevice as sd
for i,d in enumerate(sd.query_devices()):
    if d["max_input_channels"]: print(f'{i}: {d["name"]} ({d["max_input_channels"]} input channels)')
