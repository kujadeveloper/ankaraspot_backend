from elasticsearch_dsl import analyzer, token_filter, char_filter


def turkish_analyzer():
    turkish_lowercase = token_filter(
        'turkish_lowercase',
        type='lowercase',
        language='turkish'
    )
    
    # Synonyms filter tanımlama - dosya okuma yerine doğrudan tanımlama
    turkish_synonym = token_filter(
        'turkish_synonym',
        type='synonym',
        synonyms=[
            # Bilgisayar ve Donanım
            'masaüstü bilgisayar, desktop pc, bilgisayar, pc, kişisel bilgisayar, masa bilgisayarı, desktop bilgisayar, masaüstü pc',
            'laptop, dizüstü bilgisayar, notebook, taşınabilir bilgisayar, dizüstü pc, laptop bilgisayar, taşınabilir pc',
            'tablet, tabletpc, tablet bilgisayar, ipad, android tablet, dokunmatik tablet',
            'mouse, fare, bilgisayar faresi, kablosuz fare, wireless mouse, gaming mouse, oyuncu faresi, optik fare',
            'klavye, keyboard, mekanik klavye, kablosuz klavye, wireless keyboard, gaming klavye, oyuncu klavyesi',
            'ram, bellek, memory, bilgisayar belleği, hafıza',
            'işlemci, cpu, processor, merkezi işlem birimi',
            'ekran kartı, gpu, grafik kartı, graphics card, video kartı',
            'anakart, motherboard, mainboard, sistem kartı',
            'güç kaynağı, power supply, psu',
            'soğutucu, fan, cooler, bilgisayar fanı, cpu soğutucu',
            'harddisk, hard disk, hdd, ssd, depolama, storage, taşınabilir disk, external harddisk',
            'kasa, bilgisayar kasası, tower kasa, mid tower, computer case, pc kasa',
            'usb bellek, flash bellek, usb flash drive, flash disk, hafıza kartı, memory card, sd kart',
            'ağ kartı, ethernet kartı, network card, lan kartı, wifi kartı, wireless kartı',
            'ses kartı, sound card, audio kartı, dahili ses kartı, harici ses kartı',
            'bilgisayar kablosu, kablo, data kablosu, usb kablosu, hdmi kablosu, display port kablosu',
            'optik sürücü, dvd sürücü, cd sürücü, bluray sürücü, optical drive',
            'nvme ssd, m.2 ssd, sata ssd, katı hal sürücüsü, solid state drive',
            
            # Telefon ve Mobil Cihazlar
            'telefon, cep telefonu, akıllı telefon, smartphone, mobil telefon, mobil cihaz, cell phone, mobile phone, ios telefon, android telefon',
            'telefon kılıfı, cep telefonu kılıfı, telefon kabı, telefon koruyucu, phone case',
            'telefon ekran koruyucu, cam ekran koruyucu, temperli cam, screen protector',
            'akıllı telefon, smartphone, cep telefonu, android telefon, ios telefon, cep, mobil cihaz',
            'phablet, büyük ekranlı telefon, telefon tablet hibrit, büyük akıllı telefon',
            'şarj kablosu, telefon şarj kablosu, usb kablo, lightning kablo, type-c kablo, micro usb kablo',
            'hızlı şarj adaptörü, fast charger, quick charge, süper hızlı şarj, power delivery şarj',
            'telefon aksesuarı, cep telefonu aksesuarı, mobil aksesuar, telefon tutacağı, selfie ışığı',
            'telefon bataryası, cep telefonu bataryası, yedek batarya, telefon pili',
            
            # Ses ve Görüntü Sistemleri
            'kulaklık, headphone, kulakiçi kulaklık, kulak üstü kulaklık, bluetooth kulaklık, wireless kulaklık, kablosuz kulaklık, gaming kulaklık, oyuncu kulaklığı',
            'televizyon, tv, smart tv, akıllı televizyon, led tv, oled tv, 4k tv, uhd tv, hd tv, lcd tv',
            'hoparlör, speaker, ses sistemi, bluetooth hoparlör, kablosuz hoparlör, wireless speaker, soundbar, ses çubuğu',
            'monitör, ekran, bilgisayar ekranı, bilgisayar monitörü, lcd monitör, led monitör, gaming monitör, oyuncu monitörü, curved monitör, kavisli monitör',
            'mikrofon, microphone, ses kayıt cihazı, mic',
            'projeksiyon, projeksiyon cihazı, projektör, yansıtıcı',
            'amfi, amplifikatör, ses yükseltici, müzik yükseltici, power amplifier',
            'dac, dijital analog çevirici, ses işlemci, digital to analog converter',
            'av receiver, ses alıcısı, sinema alıcısı, home theater receiver',
            'kulak içi kulaklık, earbuds, kulak kanalı kulaklık, tws kulaklık, gerçek kablosuz kulaklık',
            'gürültü önleyici kulaklık, noise cancelling headphones, anc kulaklık, aktif gürültü engelleme',
            'qled tv, quantum dot tv, nanocell tv, 8k tv, android tv, webos tv, tizen tv, smart tv',
            'ev sinema sistemi, home theater, surround ses, 5.1 ses sistemi, 7.1 ses sistemi',
            'studio monitör, referans hoparlör, stüdyo hoparlör, profesyonel hoparlör',
            
            # Kamera ve Fotoğraf
            'kamera, webcam, web kamerası, dijital kamera, güvenlik kamerası, ip kamera, aksiyon kamerası, action camera',
            'fotoğraf makinesi, dslr, aynasız kamera, kompakt kamera, fotoğraf makinası',
            'kamera lensi, objektif, lens, zoom lens, makro lens',
            'tripod, kamera ayağı, selfie çubuğu, selfie stick',
            'gimbal, kamera sabitleyici, stabilizatör, elektronik sabitleyici',
            'dron, drone, uçan kamera, hava çekim aracı, quadcopter',
            'sd kart, hafıza kartı, cf kart, microsd kart, kamera hafıza kartı',
            'fotoğraf filtresi, nd filtre, uv filtre, polarize filtre, lens filtresi',
            'flaş, kamera flaşı, speedlight, stüdyo flaşı, ring light, halka ışık',
            'fotoğraf çantası, kamera çantası, lens çantası, ekipman çantası',
            'kamera bataryası, fotoğraf makinesi pili, yedek batarya, şarj edilebilir pil',
            
            # Yazıcı ve Ofis Ekipmanları
            'yazıcı, printer, lazer yazıcı, mürekkep püskürtmeli yazıcı, inkjet yazıcı, 3d yazıcı, çok fonksiyonlu yazıcı, all-in-one yazıcı',
            'tarayıcı, scanner, döküman tarayıcı, belge tarayıcı',
            'fotokopi makinesi, fotokopi cihazı, kopya makinesi',
            'kağıt, yazıcı kağıdı, a4 kağıt, ofis kağıdı',
            'toner, kartuş, mürekkep, yazıcı mürekkebi, yazıcı toneri',
            'etiket yazıcı, barkod yazıcı, termal yazıcı, termal transfer yazıcı',
            'laminasyon makinesi, laminatör, kaplama cihazı, doküman koruyucu',
            'kağıt imha makinesi, evrak imha, kağıt öğütücü, shredder',
            'ciltleme makinesi, spiralli ciltleyici, sıcak ciltleme, tel ciltleme',
            'pos cihazı, kredi kartı terminali, ödeme terminali, yazarkasa, yazar kasa',
            'projeksiyon perdesi, yansıtma perdesi, akıllı tahta, beyaz tahta, interaktif tahta',
            
            # Ağ ve Bağlantı
            'modem, router, yönlendirici, ağ cihazı, network device',
            'ethernet kablosu, ağ kablosu, internet kablosu, lan kablosu, cat6 kablo',
            'wifi adaptör, kablosuz adaptör, wireless adaptör, wifi alıcı',
            'switch, ağ anahtarı, ethernet switch',
            'mesh wifi, mesh router, whole home wifi, tüm ev kapsama, kablosuz ağ sistemi',
            'access point, erişim noktası, wifi genişletici, range extender, sinyal güçlendirici',
            'nas, network attached storage, ağ depolama, ağa bağlı depolama',
            'firewall, güvenlik duvarı, ağ güvenliği cihazı, network security',
            'ip telefon, voip telefon, internet telefonu, ağ telefonu',
            'kvm switch, klavye video mouse switch, ekran paylaşımı, bilgisayar paylaşımı',
            'fiber modem, adsl modem, vdsl modem, kablo modem, 4g modem, 5g modem',
            
            # Güç ve Şarj Ürünleri
            'şarj aleti, şarj cihazı, adaptör, güç adaptörü, power adapter, charger',
            'batarya, pil, battery, akü, güç ünitesi',
            'powerbank, taşınabilir şarj cihazı, harici batarya, yedek batarya',
            'uzatma kablosu, priz, çoklu priz, akım korumalı priz',
            'ups, kesintisiz güç kaynağı, güç yedekleme, power backup',
            'kablosuz şarj cihazı, wireless charger, qi şarj, indüksiyon şarj',
            'pil şarj cihazı, battery charger, aa pil şarj, aaa pil şarj',
            'güç çevirici, power inverter, 12v 220v çevirici, dc ac converter',
            'güneş enerjili şarj cihazı, solar şarj, güneş paneli şarj, taşınabilir solar şarj',
            'masaüstü şarj istasyonu, charging dock, çoklu şarj istasyonu, multi-device charger',
            
            # Oyun ve Eğlence
            'oyun konsolu, game console, playstation, xbox, nintendo',
            'gamepad, oyun kumandası, joystick, kontrol cihazı',
            'vr gözlük, sanal gerçeklik gözlüğü, virtual reality headset',
            'oyun, video oyunu, bilgisayar oyunu, konsol oyunu',
            'oyun direksiyonu, yarış direksiyonu, racing wheel, pedal seti',
            'arcade stick, arcade joystick, arcade controller, fight stick',
            'oyun koltuğu, gaming chair, oyuncu koltuğu, ergonomik oyun koltuğu',
            'oyun masası, gaming desk, oyuncu masası, bilgisayar oyun masası',
            'stream deck, yayın kontrol cihazı, yayıncı ekipmanı, yayın butonu',
            'artırılmış gerçeklik gözlüğü, ar gözlük, augmented reality, karma gerçeklik',
            'oyun kart okuyucu, game card reader, oyun hafıza kartı, oyun bellek kartı',
            'oyun simülatörü, uçuş simülatörü, yarış simülatörü, kokpit',
            
            # Giyilebilir Teknoloji
            'akıllı saat, smartwatch, giyilebilir saat, fitness saat',
            'akıllı bileklik, fitness bilekliği, aktivite takipçisi, activity tracker',
            'akıllı gözlük, smart glasses, artırılmış gerçeklik gözlüğü',
            'akıllı yüzük, smart ring, giyilebilir yüzük, nfc yüzük',
            'spor saati, gps saat, koşu saati, yüzme saati, triathlon saati',
            'akıllı terlik, akıllı ayakkabı, smart shoe, fitness ayakkabı',
            'akıllı giysi, e-tekstil, akıllı tişört, akıllı kıyafet, smart clothing',
            'uyku takip cihazı, sleep tracker, uyku ölçer, uyku monitörü',
            'kalp atış monitörü, nabız ölçer, ekg cihazı, heart rate monitor',
            'akıllı kask, smart helmet, bluetooth kask, iletişim kasklı',
            
            # Ev Elektroniği
            'akıllı ev sistemleri, smart home, akıllı ev cihazları',
            'elektrikli süpürge, vacuum cleaner, robot süpürge, dikey süpürge',
            'buzdolabı, refrigerator, soğutucu, derin dondurucu',
            'çamaşır makinesi, washing machine, kurutma makinesi, kurutmalı çamaşır makinesi',
            'bulaşık makinesi, dishwasher, bulaşık yıkama makinesi',
            'fırın, ocak, mikrodalga fırın, mikrodalga, oven, microwave',
            'klima, air conditioner, split klima, inverter klima',
            'ütü, buharlı ütü, ütü makinesi, iron',
            'akıllı termostat, smart thermostat, ısı kontrolü, sıcaklık düzenleyici',
            'akıllı priz, smart plug, wifi priz, uzaktan kontrollü priz',
            'akıllı aydınlatma, smart lighting, akıllı ampul, smart bulb, led ampul',
            'akıllı kilit, smart lock, parmak izi kilidi, şifreli kilit, dijital kilit',
            'akıllı perde, otomatik perde, motorlu perde, uzaktan kumandalı perde',
            'akıllı su tesisatı, akıllı musluk, dijital duş, akıllı banyo sistemi',
            'hava temizleyici, air purifier, hepa filtre, hava arıtıcı, allerjen filtresi',
            'nem alma cihazı, dehumidifier, nem alıcı, nem kontrol cihazı',
            'nemlendirici, humidifier, hava nemlendirici, buhar makinesi',
            
            # Kişisel Bakım
            'saç kurutma makinesi, fön makinesi, hair dryer',
            'tıraş makinesi, elektrikli tıraş makinesi, epilasyon cihazı',
            'elektrikli diş fırçası, sonic diş fırçası, oral care',
            'tartı, dijital tartı, vücut analiz tartısı, baskül',
            'saç şekillendirici, saç düzleştirici, düzleştirici, saç maşası, elektrikli bigudi',
            'yüz temizleme cihazı, cilt temizleme fırçası, peeling cihazı',
            'masaj aleti, masaj tabancası, kas gevşetici, masaj yastığı',
            'ağız duşu, water flosser, diş ipliği cihazı, su jeti',
            'traş makinesi, jilet, epilasyon aleti, lazer epilasyon, ışık epilasyon, ipl',
            'saç kesme makinesi, saç tıraş makinesi, saç düzeltici, sakal düzeltici',
            'cilt bakım cihazı, güzellik cihazı, led terapi, mikro akım cihazı',
            
            # Otomotiv Elektroniği
            'araç kamerası, dash cam, araç içi kamera',
            'navigasyon cihazı, gps, yol bulucu',
            'araç şarj cihazı, car charger, çakmak şarj aleti',
            'araç kiti, bluetooth araç kiti, hands-free kit',
            'obd2 cihazı, araç arıza tespit cihazı, araç tanı cihazı, diagnostik cihaz',
            'araç takip cihazı, gps tracker, araç izleme sistemi',
            'araç multimedya sistemi, double din, car play, android auto, araç ekranı',
            'araç amplifikatörü, araç amfisi, bas güçlendirici, araç ses sistemi',
            'araç hoparlörü, oto hoparlör, araç ses sistemleri, araba hoparlörü',
            'park sensörü, arka kamera, geri görüş kamerası, araç radar sistemi',
            'araç hırsız alarmı, immobilizer, araç güvenlik sistemi, uzaktan kumanda',
            
            # Akıllı Ev Güvenliği
            'güvenlik kamerası, cctv kamera, ip kamera, gözetim kamerası',
            'kapı zili kamerası, video doorbell, akıllı kapı zili',
            'alarm sistemi, güvenlik alarmı, hareket sensörü, ev güvenlik sistemi',
            'duman dedektörü, yangın alarmı, gaz dedektörü, karbon monoksit dedektörü',
            'bebek monitörü, bebek izleme cihazı, bakıcı kamerası, dijital bebek telsizi',
            'ev güvenlik paneli, alarm paneli, güvenlik kontrol ünitesi',
            
            # Ofis ve İş Ekipmanları
            'barkod okuyucu, barkod tarayıcı, qr kod okuyucu, scanner',
            'para sayma makinesi, kağıt para sayacı, bozuk para sayacı',
            'evrak rafı, dosya organizeri, ofis düzenleyici, kalem kutusu',
            'video konferans ekipmanı, konferans mikrofonu, toplantı kamerası',
            'sunum kumandası, lazer pointer, kablosuz sunum cihazı, presenter',
            'hesap makinesi, bilimsel hesap makinesi, finansal hesap makinesi',
            
            # Müzik ve Ses Ekipmanları
            'midi klavye, elektronik piyano, synthesizer, klavye enstrüman',
            'dj controller, dj mikseri, turntable, plak çalar, kaydırıcı',
            'audio interface, ses kartı, kayıt ekipmanı, stüdyo ses kartı',
            'mikser, ses mikseri, kanal mikseri, audio mixer',
            'preamp, preamplifikatör, mikrofon preamp, hat preamp',
            'stüdyo monitörü, referans hoparlör, aktif monitör, mix monitörü',
            
            # Sağlık Teknolojisi
            'dijital tansiyon aleti, tansiyon ölçer, pressure monitor',
            'şeker ölçüm cihazı, glukometre, diyabet ölçüm cihazı',
            'termometre, dijital termometre, temassız termometre, ateş ölçer',
            'tens cihazı, elektroterapi, kas stimülasyon, ağrı giderici',
            'pulse oksimetre, oksijen ölçer, kandaki oksijen seviyesi ölçer',
            'işitme cihazı, kulak içi işitme cihazı, kulak arkası işitme cihazı',
            'nebulizatör, buhar makinesi, inhalatör, solunum cihazı'
        ]
    )
    
    html_strip = char_filter('html_strip', type='html_strip')
    
    return analyzer(
        'text_analyzer',
        tokenizer='standard',
        filter=[turkish_lowercase, 'stop', 'snowball', turkish_synonym],
        char_filter=[html_strip]
    )