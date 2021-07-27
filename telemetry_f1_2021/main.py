from telemetry_f1_2021.listener import TelemetryListener


def main():
    try:
        print('Starting listener on localhost:20777')
        listener = TelemetryListener()
    except OSError as exception:
        print(f'Unable to setup connection: {exception.args[1]}')
        print('Failed to open connector, stopping.')
        exit(127)

    try:
        while True:
            print(listener.get())
    except KeyboardInterrupt:
        print('Stop the car, stop the car Checo.')
        print('Stop the car, stop at pit exit.')
        print('Just pull over to the side.')


if __name__ == '__main__':
    main()
