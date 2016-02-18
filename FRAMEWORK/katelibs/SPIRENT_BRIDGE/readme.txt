utore: L Cutilli 
#  Data:   18/02/2016
#
#

I file presenti in questa directory implementano
un server per il controllo di strumenti Spirent TestCenter
tramite la libreria k@te "instrumentSTC"
L'utilizzo di Bridge e Coorodinator implica
la presenza di una macchina virtuale implementata ad hoc

Ulteriori dettagli di seguito.
 
 
 
Macchina col Bridge e il coordinator: 151.98.52.74
 Utente root/alcatel -> macchina ORIGINALE, non chroottata
 Con questo utente vedo la macchina reale:
 -bash: 52.74ll: command not found
  [root@it052074 /]# ll
  total 182
  drwxr-xr-x   2 root root  4096 Jan 28 16:34 151.098.016.007__repository
  drwxr-xr-x   2 root root  4096 Feb  9 04:02 bin
  drwxr-xr-x   4 root root  1024 Dec 23 08:56 boot
  drwxr-xr-x  14 root root  3640 Jan 15 10:19 dev
  drwxr-xr-x   4 root root  4096 Jan 15 16:37 dklocal  <--- LA MACCHINA CHROOTTATA
  drwxr-xr-x  99 root root 12288 Feb 17 04:02 etc           SI TROVA QUI DENTRO E CI
  drwxr-xr-x   6 root root  4096 Jan 25 15:49 home          SI ENRA LOGGANDOSI COME LORE O ANDREA
  drwxr-xr-x  11 root root  4096 Jan 21 11:15 lib
  drwxr-xr-x   8 root root 12288 Feb  9 04:02 lib64
  drwx------   2 root root 16384 Dec 23 09:51 lost+found
  drwxr-xr-x   2 root root  4096 Oct  1  2009 media
  drwxr-xr-x   2 root root     0 Jan 15 10:19 misc
  drwxr-xr-x   2 root root  4096 Oct  1  2009 mnt
  drwxr-xr-x   2 root root     0 Jan 15 10:19 net
  drwxr-xr-x   2 root root  4096 Oct  1  2009 opt
  dr-xr-xr-x 125 root root     0 Jan 15 10:18 proc
  drwxr-x---   8 root root  4096 Feb 17 14:34 root
  drwxr-xr-x   2 root root 12288 Feb  9 04:02 sbin
  drwxr-xr-x   2 root root  4096 Dec 23 08:51 selinux
  drwxr-xr-x   2 root root  4096 Oct  1  2009 srv
  drwxr-xr-x  11 root root     0 Jan 15 10:18 sys
  drwxr-xr-x   3 root root  4096 Dec 23 08:55 tftpboot
  drwxrwxrwt   6 root root  4096 Feb 17 04:02 tmp
  drwxr-xr-x  15 root root  4096 Dec 23 08:53 usr
  drwxr-xr-x  23 root root  4096 Dec 23 08:58 var

  Il path assoluto REALE della macchina chroottata e' il seguente:
  /dklocal/151.098.016.007__simulator_rootdir/
                 
  Loggandoci come lore o andrea vediamo il path sopra come fosse root "/" 
  
Utenti per eseguire STCBridge.py e STCBridge_Coordinator.py:
 Utente lore/alcatel   -> macchina chroottata:  <-- ok per bridge/coordinator ma usare utente andrea
 Utente andrea/alcatel -> macchina chroottata: <-- USARE ANDREA!
Come lanciare il coordinator:
 # ssh andrea@151.98.52.74
   (pwd: alcatel)
 # smo (e' un alias di "cd /SMO_Tools")
 # /users/TOOLS/LINUX/ActivePython/bin/python ./STCBridge_Coordinator.py & 
 oppure solamente 
 # ./STCBridge_Coordinator.py & 

A questo punto la libreria instrumentSTC.py e' pronta per essere utilizzata.
 



