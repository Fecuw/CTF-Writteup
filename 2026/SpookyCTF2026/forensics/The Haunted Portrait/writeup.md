# Writeup
"Students claim the painting changes when viewed at night, and some believe a secret message is hidden inside it." We get `haunted_portrait.png`.

"changes when viewed differently" = bit planes. I load it into StegOnline (georgeom.net/StegOnline) and flip through the bit planes. On the **Blue channel, bit 0**, hidden text shows up:

```
THE PORTRAIT WHISPERS:
THE DEAD SPEAK IN ROT13
fcbbxl{cbegenvgf_xrrc_frpergf}
```

So the message tells us it's ROT13. Decode it:

```python
import codecs
print(codecs.decode("fcbbxl{cbegenvgf_xrrc_frpergf}", "rot13"))
# spooky{portraits_keep_secrets}
```

# flag
```
spooky{portraits_keep_secrets}
```
