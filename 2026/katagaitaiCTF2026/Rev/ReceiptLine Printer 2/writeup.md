# Writeup
どうやらflagを含む出力は全て弾かれるらしい

もしかしてflagを断片的に取り出せばチェッカーは認識しないのでは？

切り出しをやってみる
```code
{text:nowrap}
{width:10}
${FLAG}
```

![alt](./img/スクリーンショット%202026-11-07%2016.18.30.png)

いけそうだな

```code
{text:nowrap}
{width:15}
${FLAG}
```

![alt](./img/58e95281-7c5d-4f6f-ba6e-98555601bb6c.png)

長いな...

![alt](./img/a2acaf94-941b-4acb-a874-8814781cc838.png)

ここまでで止まってしまった...

guessするか

どうやら二文字か三文字ラストで途切れそうなのでそれで終わる単語を考える

leet未使用っぽいのでPix->Pixel?

submitするとあってるらしい


# flag
```
FLAG{CheckImagePixel}
```