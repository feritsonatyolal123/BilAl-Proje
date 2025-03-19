from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)

# Veritabanı bağlantısı
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite veritabanı
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

# SQLAlchemy'i başlatıyoruz
db = SQLAlchemy(app)

# Kullanıcı Modeli (Veritabanı tablosu)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Bilet Modeli (Veritabanı tablosu)
class Ticket(db.Model):
    ticket_number = db.Column(db.Integer, primary_key=True)
    cinema = db.Column(db.String(100), nullable=False)
    seat = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    film = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)

# Veritabanını oluştur (ilk başta çalıştırın)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Boş alan kontrolü
        if not username or not password:
            flash('Kullanıcı adı ve şifre boş olamaz!', 'error')
            return redirect(url_for('login'))
        
        # Kullanıcıyı veritabanından sorguluyoruz
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):  # Hashlenmiş şifreyi kontrol ediyoruz
            session['username'] = user.username  # Kullanıcı adı oturumda saklanır
            return redirect(url_for('ticket'))
        else:
            flash('Kullanıcı adı veya şifre yanlış', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Boş alan kontrolü
        if not username or not email or not password:
            flash('Tüm alanlar doldurulmalıdır!', 'error')
            return redirect(url_for('register'))
        
        # Email'in zaten var olup olmadığını kontrol et
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Bu email adresi zaten kullanılıyor. Lütfen başka bir email girin.', 'error')
            return redirect(url_for('register'))
        
        # Şifreyi hashliyoruz
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Yeni kullanıcıyı veritabanına ekliyoruz
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/ticket', methods=['GET', 'POST'])
def ticket():
    if request.method == 'POST':
        film = request.form['film']
        return render_template('buy.html', film_title=film)
    return render_template('ticket.html')

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'POST':
        try:
            cinema = request.form['cinema']  # 'cinema' form verisinin doğru gönderildiğinden emin olun
            seat = request.form['seat']
            time = request.form['time']
            film = request.form['film']  # Film bilgisi alınır

            # Kullanıcı adı oturumdan alınır
            username = session.get('username')
            if not username:
                flash('Lütfen giriş yapın.', 'error')
                return redirect(url_for('login'))
            
            ticket_number = random.randint(100000, 999999)
            
            # Yeni bilet kaydını veritabanına ekliyoruz
            ticket_info = Ticket(ticket_number=ticket_number, cinema=cinema, seat=seat, time=time, film=film, username=username)
            db.session.add(ticket_info)
            db.session.commit()
            
            return redirect(url_for('thanks', ticket_number=ticket_number))
        
        except KeyError as e:
            flash(f"Form verisi eksik: {str(e)}", 'error')
            return redirect(url_for('buy'))  # Hata olması durumunda formu tekrar gösterir.
    
    return render_template('buy.html')

@app.route('/thanks', methods=['GET', 'POST'])
def thanks():
    if request.method == 'POST':
        cinema = request.form['cinema']
        seat = request.form['seat']
        time = request.form['time']
        film = request.form['film']  # Film bilgisi alınır

        # Kullanıcı adı oturumdan alınır
        username = session.get('username')
        if not username:
            flash('Lütfen giriş yapın.', 'error')
            return redirect(url_for('login'))
        
        ticket_number = random.randint(100000, 999999)
        
        # Yeni bilet kaydını veritabanına ekliyoruz
        ticket_info = Ticket(ticket_number=ticket_number, cinema=cinema, seat=seat, time=time, film=film, username=username)
        db.session.add(ticket_info)
        db.session.commit()
        
        return render_template('thanks.html', ticket_info=ticket_info)
    
    # Eğer GET isteği ise
    ticket_number = int(request.args.get('ticket_number'))
    ticket_info = Ticket.query.get(ticket_number)
    
    return render_template('thanks.html', ticket_info=ticket_info)


@app.route('/goruntule', methods=['GET', 'POST'])
def goruntule():
    if request.method == 'POST':
        ticket_number = request.form['ticket_number']
        
        # Veritabanından bilet bilgisini çek
        ticket_info = Ticket.query.filter_by(ticket_number=ticket_number).first()
        
        if ticket_info:
            return render_template('goruntule.html', ticket_info=ticket_info)
        else:
            return render_template('goruntule.html', error="Böyle bir bilet bulunamadı.")
    
    return render_template('goruntule.html')


if __name__ == '__main__':
    app.run(debug=True)
