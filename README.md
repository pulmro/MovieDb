MovieCase
=========

MovieCase is an application that scans your movies file collection and collect info from the web (themoviedb.org) and gives you a nice gui.
It has also a server running a minimal REST api to interact with it.

It's written in python and now it uses CherryPy and Flask (>=0.9) for the internal server and web interface respectively.
It's born essentially as an experiment to improve my python (and php once upon) skills and as a need to handle my movie collection files stored in my home sheevaplug server and shared with roommates.

It needs:

* PyTMDB3 ( [pytmdb3](https://github.com/wagnerrp/pytmdb3) )

* CherryPy

* Flask (>= 0.9)

* SQLAlchemy

Screenshots of the web gui:

<div style="float:left">
<img src="https://raw.github.com/pulmro/moviecase/master/docs/moviecase1.png" alt="Home page with the movie list" height=200/>
</div>
<div style="float:right">
<img src="https://raw.github.com/pulmro/moviecase/master/docs/moviecase2.png" alt="Movie detail page" height=200/>
</div>
