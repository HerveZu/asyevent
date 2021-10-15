<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/HerveZu/asyevent">
    <h1 align="center">Asyevent</h1>
  </a>

  <p align="center">
    An implementation of events and asynchronous callbacks using decorators.
    <br />
    <br />
    <a href="https://github.com/HerveZu/asyevent/issues">Report Bug</a>
    ·
    <a href="https://github.com/HerveZu/asyevent/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-using">Built using</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

An implementation of events and asynchronous callbacks using decorators.
The project is currently in development. 
The main features are stables and work perfectly as I've tested,
but if you notice any issue, or you have a suggestion to make, it's 
greatly appreciated.

### Built using

* [asyncio](https://github.com/python/asyncio/tree/master)



<!-- GETTING STARTED -->
## GETTING STARTED

## Installation
```sh
pip install asyevent
```



<!-- USAGE EXAMPLES -->
## Usage

```py
import asyncio
from asyevent import EventManager


# creates a main event manager
manager = EventManager()

# creates an event
sample_event = manager.create_event("sample_event")


# adds `call_on_event` coroutine as sample_event's callback
@sample_event.as_callback()
async def sample_event_callback(text: str):
    print(text)
    await asyncio.sleep(2)


# uses `.after` event which refers to an event that is raised
# when the parent event's callbacks are ended (data_lost)
@sample_event.after().as_callback()
async def after_event(time_took: int, *args):
    # invokes the command `say`
    await manager.invoke_command("say", f"I've been here for {time_took} seconds")


# adds the `say_stm` coroutine as a callback of the command `say_hello`
@manager.as_command(name="say")
async def say_stm(name: str):
    print(f"Hello, {name} !")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # raises the event `sample_event`
    loop.run_until_complete(sample_event("Hello, world !"))

```
_More example in `asyevent/examples/` folder._


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/HerveZu/asyevent/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

[Zucchinetti Hervé](mailto:herve.zucchinetti@gmail.com)

[GitHub](https://github.com/HerveZu/asyevent)

#
[Readme template](https://github.com/othneildrew/Best-README-Template)