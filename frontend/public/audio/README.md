# Drop real audio here

The iPod on the landing page plays original synthesised loops out of the box, so
nothing needs to be here for it to work.

To play a real song instead, put the file in this folder and point a track at it
in `src/lib/tracks.ts`.

The first track is already wired up and waiting for:

    public/audio/sunflower.mp3

Drop that file in and reload — the iPod plays it automatically. Until then it
falls back to the built-in loop and says so on screen.

## Adding more

```ts
// src/lib/tracks.ts
{
  title: "My Song",
  artist: "Someone",
  album: "An Album",
  src: "/audio/my-song.mp3",   // optional
  synth: { ... },              // required fallback
}
```

## Licensing

Only add audio you own or are licensed to distribute. Nothing copyrighted ships
in this repo, and shipping a commercial track on a public marketing page without
a licence is copyright infringement — get the rights first.
