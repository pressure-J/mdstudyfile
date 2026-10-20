---
attachments: [屏幕截图 2025-09-15 202214.png, 屏幕截图 2025-09-15 202538.png, 屏幕截图 2025-09-15 202604.png, 屏幕截图 2025-09-15 202626.png, Clipboard_2025-09-15-21-01-00.png]
title: cyperhack基础题目详解
created: '2025-09-15T12:07:52.607Z'
modified: '2025-10-16T14:00:25.390Z'
---

# cyperhack基础题目详解
## 1
[第1题](https://cryptohack.org/courses/intro/enc1/)
![](@attachment/屏幕截图 2025-09-15 202214.png)
如图所示，编写代码
```python
a=[99, 114, 121, 112, 116, 111, 123, 65, 83, 67, 73, 73, 95, 112, 114, 49, 110, 116, 52, 98, 108, 51, 125]
c=bytes(a)
print(c)
```
得出结果 crypto{ASCII_pr1nt4bl3}
## 2
[第2题](https://cryptohack.org/courses/intro/enc2/)
![](@attachment/屏幕截图 2025-09-15 202538.png)
如图所示，编写代码
```python
a='63727970746f7b596f755f77696c6c5f62655f776f726b696e675f776974685f6865785f737472696e67735f615f6c6f747d'
b=bytes.fromhex(a)
print(b)
```
得出结果crypto{You_will_be_working_with_hex_strings_a_lot}
## 3
[第3题](https://cryptohack.org/courses/intro/enc3/)
![](@attachment/屏幕截图 2025-09-15 202604.png)
如图所示，编写代码
```python
import base64
a='72bca9b68fc16ac7beeb8f849dca1d8a783e8acf9679bf9269f7bf'
b=bytes.fromhex(a)
c=base64.b64encode(b)
print(c)
```
得到结果crypto/Base+64+Encoding+is+Web+Safe/
## 4
[第4题](https://cryptohack.org/courses/intro/enc4/)
![题目](@attachment/Clipboard_2025-09-15-21-01-00.png)
如图所示，编写代码
```python
from Crypto.Util.number import*
a=11515195063862318899931685488813747395775516287289682636499965282714637259206269
b=long_to_bytes(a)
print(b)
```
得到结果crypto{3nc0d1n6_4ll_7h3_w4y_d0wn}
