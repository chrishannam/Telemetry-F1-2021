from telemetry_f1_2021.listener import TelemetryListener


def main():
    try:
        listener = TelemetryListener()
    except OSError as exception:
        print(f'Unable to setup connection: {exception.args[1]}')
        print('Failed to open connector, stopping.')
        exit(127)

    while True:
        print(listener.get())


if __name__ == '__main__':
    main()
