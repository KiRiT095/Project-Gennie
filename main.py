from app.bodies.desktop.body import DesktopBody


def main() -> int:
    body = DesktopBody()
    return body.run()


if __name__ == "__main__":
    raise SystemExit(main())
