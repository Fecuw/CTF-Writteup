# Writeup
"Maybe the photo contains the answer." We get `TormentedTanny.png`.

The hint is about the photo itself, so I dump all the metadata with exiftool:

```bash
exiftool -a -u -G1 -s TormentedTanny.png
```

The flag is split across three different metadata fields:

```
[PNG]     Title            : spooky{tormented_tanner_
[XMP-dc]  Description      : hates_his_
[IFD0]    ImageDescription : vetsulin}
```

Just stick the three pieces together in order:

```
spooky{tormented_tanner_} + hates_his_ + vetsulin}
-> spooky{tormented_tanner_hates_his_vetsulin}
```

# flag
```
spooky{tormented_tanner_hates_his_vetsulin}
```
