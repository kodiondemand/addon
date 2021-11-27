# sorry for obfuscation, it's for making a little more difficult for maxstream owner to counter this

import ast ,sys
import base64 
if sys .version_info [0 ]>=3 :
    import urllib .parse as urlparse 
else :
    import urlparse 
from core import httptools ,scrapertools ,support 
from lib import jsunpack 
from platformcode import logger ,config ,platformtools 
def decode (OOO000OOOO0OOOOOO ):
 OOO0OOOO0O00OOOOO =[]
 OOO000000OOO000OO =__name__ 
 OOO000OOOO0OOOOOO =base64 .urlsafe_b64decode (OOO000OOOO0OOOOOO ).decode ()
 for OOO0OO0O000OOO0OO in range (len (OOO000OOOO0OOOOOO )):
  OO0OOOO0O0O0OO000 =OOO000000OOO000OO [OOO0OO0O000OOO0OO %len (OOO000000OOO000OO )]
  O0OO0O0O00OOOOOO0 =chr ((256 +ord (OOO000OOOO0OOOOOO [OOO0OO0O000OOO0OO ])-ord (OO0OOOO0O0O0OO000 ))%256 )
  OOO0OOOO0O00OOOOO .append (O0OO0O0O00OOOOOO0 )
 return "".join (OOO0OOOO0O00OOOOO )
headers ={decode ('w4jDmMOXw6jCksKzw5rCk8Obw5U='):decode ('w4DDlMOsw5_DkcOew5RdwqLCj8KowpPCnMK-w47Dj8Oiw6vCoMKSwrfDk8OWw6XCncOWw4XCmMKkwqXCm8KFwqLDncOjw5HDl8ONw4rDlMK-wpfDocKQwq3CpsKrwqDCmMKXwo3Cm8KwwrrDisKywr7Cn07DmcOKw6PDmMKUwrnDisOEw5jDosKOwpLCucONw6TDosKbw5LCkMKxwqTCosKiwpPClcKhwqrCl8KgwqfCl8KiwpN7w5zDg8Ohw5_DmcKSwrjDgsOTw5TDl8ObwqXCmsKlwqpcwqDClw==')}
def test_video_exists (page_url ):
    logger .debug (page_url )
    global data ,new_url 
    new_url =httptools .downloadpage (page_url ,follow_redirects =False ,cloudscraper =True ,alfa_s =True ).headers .get (decode ('w5_DlMOVw5fDmcObw6LCnA=='),page_url )
    data =httptools .downloadpage (new_url ,cloudscraper =True ,alfa_s =True ).data 
    if scrapertools .find_single_match (data ,decode ('wpvCpMKuwpfDk8Ohw6HCk8KWwpzDk8ORwrLDj8KPwp_Dk8Ocw5HDl8KWw5zDk8OmTsORw4bDpMOYw6jDl8OJ')):
        return False ,config .get_localized_string (70449 )%decode ('w4DDhsOqw4nDmcOkw5jCj8Oa')
    return True ,""
def get_video_url (page_url ,premium =False ,user ="",password ="",video_password =""):
    global data ,new_url ,code 
    page_url =new_url 
    logger .debug (decode ('w6jDl8OewrM=')+page_url )
    code =scrapertools .find_single_match (data ,decode ('wpvCpMKsw57DmcOmw6PCocKnwpDCp8Ogw5XDqsOYw5XDn8OYw4bDn8Kkw5vDm8OXwpPDnMKQw5zCosOww6DDhsOOw5LCsMKHw5vDmsKHwpLDqcKPw5nDlsOdwrDClsKbwo3CvMOLwpXDgsKdwp8='))
    O0OO00OOOOOOO00O0 =httptools .downloadpage (decode ('w5vDmcOmw6bDmMKswqJdw5rDgsOww6bDqMOkw4rDgsOawqHDm8Obw5rDisOhwqLCk8Oaw4PDncOXwqE=')+code +decode ('wqHDjcOmw6PDkQ=='),cloudscraper =True ,alfa_s =True ,headers =headers ).data 
    O0000000O00O0O000 =httptools .downloadpage (decode ('w5vDmcOmw6bDmMKswqJdw5rDgsOww6bDqMOkw4rDgsOawqHDm8Obw5rDisOhwqLCk8Oaw4PDncOXwqHDk8KYw5vDnsOnw5LCp8Oqw57DmcOmwpnCm8OJw6zDoMOg'),cloudscraper =True ,alfa_s =True ,headers =headers ).data 
    O0OOOOO0O0OOO00OO =scrapertools .find_multiple_matches (O0OO00OOOOOOO00O0 ,decode ('w5fDhsOmw5fCksOlw5zCosOSw4zDncOswrHDjcKMwoPDisKTwo_CmsORw4PClMKawovCmMKK'))
    if O0OOOOO0O0OOO00OO :
        O0OOOOO0O0OOO00OO =O0OOOOO0O0OOO00OO [-1 ]
        OOOO00O00OO000O00 =platformtools .show_recaptcha (O0OOOOO0O0OOO00OO ,new_url )
        if not OOOO00O00OO000O00 :
            platformtools .play_canceled =True 
            return []
        OOOO0O0O0000O00OO =scrapertools .find_multiple_matches (data ,decode ('wq_DjsOgw6bDmsOmwqFYwqzCicK3wq3DosOTw5LDhsKqw47Ch8KZw5PCjcONw5FVwo_CvsKjwpzCosKcwqTDl8OOw5_DmsOXwrPDgMKUwprCi8KVwrzDlsKawpbDj8KPworDiMKawofDj8K0w6HCsMKc'))
        if OOOO0O0O0000O00OO :
            O00OO000000000000 ={O0000O000OOOO00O0 [0 ]:O0000O000OOOO00O0 [1 ]for O0000O000OOOO00O0 in OOOO0O0O0000O00OO if O0000O000OOOO00O0 [0 ]}
            if OOOO00O00OO000O00 :O00OO000000000000 [decode ('w5rCksOkw5vDiMOTw6PCosOQw4nDmcKgw6bDl8OYw5HDnMOhw5jDlw==')]=OOOO00O00OO000O00 
            if O00OO000000000000 :
                data =httptools .downloadpage (page_url ,post =O00OO000000000000 ,follow_redirects =True ,cloudscraper =True ,alfa_s =True ,headers =headers ).data 
        else :
            platformtools .dialog_ok (config .get_localized_string (20000 ),config .get_localized_string (707434 ))
            return []
    try :
        O0O0O00000000OOOO =method_1 (O0OO00OOOOOOO00O0 )
        O0OO000OO0000O00O =method_1 (O0000000O00O0O000 )
        if not O0O0O00000000OOOO or O0O0O00000000OOOO [0 ][1 ].split (decode ('wp8='))[0 ]==O0OO000OO0000O00O [0 ][1 ].split (decode ('wp8='))[0 ]:
            O0O0O00000000OOOO =method_1 (data )
            O0OO000OO0000O00O =method_1 (httptools .downloadpage (decode ('w5vDmcOmw6bDmMKswqJdw5rDgsOww6bDqMOkw4rDgsOawqHDm8Obw5rDisOhwqLCj8Kgw5vDqcOnw6HCp8OZw5rDlMOmw5A='),cloudscraper =True ,alfa_s =True ).data )
    except :
        O0O0O00000000OOOO =[]
        O0OO000OO0000O00O =[]
        pass
    if not O0O0O00000000OOOO or (O0OO000OO0000O00O and O0O0O00000000OOOO[0][1].split(decode ('wp8='))[0] == O0OO000OO0000O00O[0][1].split(decode ('wp8='))[0]):
        O0O0O00000000OOOO =method_2 ()
    if not O0O0O00000000OOOO :
        O0O0O00000000OOOO =method_3 ()
    return O0O0O00000000OOOO 
def method_1 (O0O000OO00OOO0OOO ):
    OOOOO0O00OOOO0OOO =support .match (O0O000OO00OOO0OOO ,patron =decode ('wpvDisOow5fDkcOOwpvClMOiw4_Dm8Onw53DocOTwr3ClcOjwpHDk8Kiw4jCnsOeWsOSwo3DnMOPwp3CoMKPwqDClsOPw5jCnMKywpTDpcOWwqDDlsORw6w=')).matches 
    if OOOOO0O00OOOO0OOO and len (OOOOO0O00OOOO0OOO )==1 :
        O0O0O00O00OO0O0O0 =jsunpack .unpack (OOOOO0O00OOOO0OOO [0 ])
        O0OOO0OOO00O000OO =scrapertools .find_single_match (O0O0O00O00OO0O0O0 ,decode ('w6bDl8OVwrDDgcOlwp1QwpXCvMOWwpXDkcKdwo4='))
        if O0OOO0OOO00O000OO :
            return [[decode ('w6DCmMOnwq7ChcONw4DCj8OlwrTDrMOlw5nDk8OSwr4='),O0OOO0OOO00O000OO ]]
    return []
def method_2 ():
    global data ,new_url ,code 
    O000O0O000O0OOO0O =support .match (data ,patron =decode ('wq_DhsONw5TCocOPwp7ClsOfw4bDnsKwwpbCmsKkwpvDlcOnw5nDosOpwp_CocKiwpvDjsOZw6vDp8Omw5fDhsOOw4nCocObw5vDmsOKw6HColfCrMKJw5PDkcKWwqDCpMK-wpjCosKO')).matches 
    for OOOO0O00OO0OOO00O in O000O0O000O0OOO0O :
        if OOOO0O00OO0OOO00O ==decode ('w5vDmcOmw6bDmMKswqJd'):
            continue 
        data =httptools .downloadpage (decode ('w5vDmcOmw6bCn8KhwqLCm8OOw5nDq8Onw6bDl8OGw47Cm8Opw47DlsObw5TCoQ==')+OOOO0O00OO0OOO00O +code ,cloudscraper =True ,alfa_s =True ).data 
        OO00OO00O00000O0O =""
        O0OOO0O00O0000O00 =data .rfind (decode ('wq_DmMOVw6jDjsOiw6ds'))
        O00OO0O0000O000OO =data .rfind (decode ('wq_ClMOlw5nDl8Obw6PCosKr'))
        O000OOO0O0000OOO0 =data [(O0OOO0O00O0000O00 +len (decode ('wq_DmMOVw6jDjsOiw6ds'))):O00OO0O0000O000OO ]
        O0O0O000O00O0OOO0 =scrapertools .find_single_match (O000OOO0O0000OOO0 ,decode ('wpvDgcONw5HDg8OOw5DCi8KYwr3DlcKcw4_DkMOBw5zDisKdw4HDrcORw4PDjsKbwovCmMK9wqDDo8OVw6TDmMOGwrbDocOZw47CnsObw5PDn8Kjw5LCvcKhw4_Dp8KxwpLCvcOgwrLCjcONwqbCksKrw5BZwpY='))
        if O0O0O000O00O0OOO0 :
            O000OOOO0OO0OO000 =ast .literal_eval (O0O0O000O00O0OOO0 [0 ])
            O0O0O0OO0O00O00OO ="".join ([chr (OO000O00OOO0O00O0 -int (O0O0O000O00O0OOO0 [1 ]))for OO000O00OOO0O00O0 in O000OOOO0OO0OO000 ])
            O0OOOO0O00O00OOO0 =scrapertools .find_single_match (O0O0O0OO0O00O00OO ,decode ('w4_CicKgw53DisOmw49Ww4nCiMKgw47DksOOwozCvsKYwpw=')).replace (decode ('w5vDmcOmw6bDmMKswqJd'),decode ('w5vDmcOmw6bCn8KhwqI='))
            OO0O00OOOO0OO0O00 =httptools .downloadpage (O0OOOO0O00O00OOO0 ,headers ={decode ('w6vCksOkw5vDlsOnw5jCocOhw4bDnMKgw6vDm8OZw4k='):decode ('w4vCssK-wr7DmcOmw6PCgMOSw5LDrcOYw6fDpg=='),decode ('w4XDisOYw5vDl8OXw6U='):new_url },cloudscraper =True ,alfa_s =True ).data 
            OO00OO00O00000O0O =scrapertools .find_single_match (OO0O00OOOO0OO0O00 ,decode ('w5bDiMOOwqTDiMOTw6bCosOJwonCn8Kbw5zDpsOZw5HDiMOmw4LCscKkw4DDkMKawovCmMKKwp8='))
        else :
            logger .debug (decode ('w4bDlMOfw5vDmcOaw5zCnMOUwoHDr8Olw6PDoMOMwpvCjcOhw5TCksOrw5fDnsKTwpTDnMOWw6bDl8KUw5TDisOHw5zDpcOKwpLDqsONw5PDp07Cp8KJ'))
        if OO00OO00O00000O0O and OO00OO00O00000O0O .split (decode ('wqI='))[-1 ]==code :
            import random ,string 
            O0000000O00OOOOO0 =urlparse .urlparse (OO00OO00O00000O0O )
            O00O0O0O0OOOO0O0O =[[decode ('w6DDlcKmwpbDgMK_w5TCpsOAw5XDqsOYw5XDn8OC'),OO00OO00O00000O0O ]]
            try :
                O000O000O0O000OO0 ="".join (random .choice (string .ascii_letters +string .digits )for O00OO0O000O0OO0OO in range (19 ))
                OOO000O0O0O000OO0 ="".join (random .choice (string .ascii_letters +string .digits )for O0OO000O0OO0O0000 in range (19 ))
                O0O0O0O000O0OO00O ="".join (random .choice (string .ascii_letters +string .digits )for OOOOOOO00OOOO0O0O in range (19 ))
                O00O0O0O0OOOO0O0O .append ([decode ('w6DCmMOnwq7ChcONw4DCj8OlwrTDrMOlw5nDk8OSwr4='),decode ('w67DosKswqXClMOtw7Bdw5XDjcOrwqLDr8OvwpHDnMOqwp_DoMOvwqLDoMOvwp9cw6LDk8Okw6bDmcOmwpTDjsOOw6bDmcOXw6jCk8OfwqbCo8Kl').format (O0000000O00OOOOO0 .scheme ,O0000000O00OOOOO0 .netloc ,O0000000O00OOOOO0 .path .split (decode ('wqI='))[1 ],O000O000O0O000OO0 ,OOO000O0O0O000OO0 ,O0O0O0O000O0OO00O )])
            except :
                logger .debug (decode ('w4bDlMOfw5vDmcOaw5zCnMOUwoHDr8Olw6PDoMOMwpvCjcK8w5LDosOlw5jDpcOcwpDDmcOGwpjDmsOZw6bChcKpwrnDhsKFw6XDqsOXw5fDlMKb'))
    return []
def method_3 ():
    httptools .set_cookies ({decode ('w6HDhsOfw5s='):decode ('w5fDnA=='),decode ('w6nDhsOew6vDig=='):decode ('wqQ='),decode ('w5fDlMOfw5fDjsOg'):decode ('w6DDhsOqw6nDmcOkw5jCj8Oawo_DrsOcw5jDl8OU')},False )
    OOOO0OOOO0000OOO0 =httptools .downloadpage (decode ('w5vDmcOmw6bDmMKswqJdw5rDgsOww6bDqMOkw4rDgsOawqHDm8Obw5rDisOhwqLCksOcw5jDpsOfw6PDk8OJwpDDlsOhw5jDm8Oaw4rDmMOlwpPDksOZwqbDo8Ocw6LCpMOJw6bDn8Ki')+base64 .b64encode (decode ('wqjClcKiw7LDoMOv').format (code ).encode ()).decode (),timeout =10 ,cloudscraper =True ,alfa_s =True ,headers ={decode ('w4vCksOEw5vDlsOnw5jCocOhw4bDnMKgw4vDm8OZw4k='):decode ('w4vCssK-wr7DmcOmw6PCgMOSw5LDrcOYw6fDpg=='),decode ('w4XDisOYw5vDl8OXw6U='):decode ('w5vDmcOmw6bDmMKswqJdw5rDgsOww6bDqMOkw4rDgsOawqHDm8Obw5rDisOhwqLCksKc')+code }).data 
    OO0OOO000O0O000O0 =scrapertools .find_single_match (OOOO0OOOO0000OOO0 ,decode ('wrfDlMOpw6TDkcOhw5TCksKNwqnDocOaw5zCksKpw4bDk8Ocw5PDm8Oqw47DocOhXMKXwqDCtMOUwpTDmsOXw4bDk8KwwozCmsORw4PCmcOQWcKW'))
    if OO0OOO000O0O000O0 :
        return [[decode ('w6DDlcKmwpbDgMK_w5TCpsOAw5XDqsOYw5XDn8OC'),OO0OOO000O0O000O0 ]]
    return []
