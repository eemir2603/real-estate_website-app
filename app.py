import os
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'liman.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-degistir-bunu')

ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'liman2026'))

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)          # slug: mersin, girne, ...
    city_label = db.Column(db.String(120), nullable=False)   # "Mersin, Yenişehir"
    region = db.Column(db.String(10), nullable=False)        # tr | kktc
    property_type = db.Column(db.String(30), nullable=False) # Daire | Villa | Arsa | İşyeri
    tier = db.Column(db.String(10), nullable=False)          # eco | orta | ust
    status = db.Column(db.String(20), nullable=False)        # Satılık | Kiralık | Yatırımlık
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), nullable=False, default='TRY')
    area_m2 = db.Column(db.Integer, nullable=False)
    rooms = db.Column(db.String(20), nullable=False)
    floor_info = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'city': self.city,
            'city_label': self.city_label, 'region': self.region,
            'property_type': self.property_type, 'tier': self.tier,
            'status': self.status, 'price': self.price, 'currency': self.currency,
            'area_m2': self.area_m2, 'rooms': self.rooms, 'floor_info': self.floor_info,
        }


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Public site
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
@app.route('/api/listings')
def api_listings():
    q = Listing.query
    region = request.args.get('region')
    city = request.args.get('city')
    ptype = request.args.get('type')
    tier = request.args.get('tier')
    if region:
        q = q.filter_by(region=region)
    if city:
        q = q.filter_by(city=city)
    if ptype:
        q = q.filter_by(property_type=ptype)
    if tier:
        q = q.filter_by(tier=tier)
    listings = q.order_by(Listing.created_at.desc()).all()
    return jsonify([l.to_dict() for l in listings])


@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email:
        return jsonify({'error': 'Ad ve e-posta zorunludur.'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Geçerli bir e-posta girin.'}), 400

    msg = ContactMessage(name=name, email=email, phone=phone, message=message)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('Hatalı şifre, tekrar dene.')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


# ---------------------------------------------------------------------------
# Admin dashboard + CRUD
# ---------------------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    listings = Listing.query.order_by(Listing.created_at.desc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread_count = ContactMessage.query.filter_by(is_read=False).count()
    return render_template('admin_dashboard.html', listings=listings, messages=messages,
                            unread_count=unread_count)


@app.route('/admin/listings/new', methods=['POST'])
@admin_required
def admin_new_listing():
    f = request.form
    listing = Listing(
        title=f['title'], city=f['city'], city_label=f['city_label'],
        region=f['region'], property_type=f['property_type'], tier=f['tier'],
        status=f['status'], price=float(f['price']), currency=f['currency'],
        area_m2=int(f['area_m2']), rooms=f['rooms'], floor_info=f['floor_info'],
    )
    db.session.add(listing)
    db.session.commit()
    flash('İlan eklendi.')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/listings/<int:listing_id>/edit', methods=['POST'])
@admin_required
def admin_edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    f = request.form
    listing.title = f['title']; listing.city = f['city']; listing.city_label = f['city_label']
    listing.region = f['region']; listing.property_type = f['property_type']; listing.tier = f['tier']
    listing.status = f['status']; listing.price = float(f['price']); listing.currency = f['currency']
    listing.area_m2 = int(f['area_m2']); listing.rooms = f['rooms']; listing.floor_info = f['floor_info']
    db.session.commit()
    flash('İlan güncellendi.')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/listings/<int:listing_id>/delete', methods=['POST'])
@admin_required
def admin_delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    flash('İlan silindi.')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/messages/<int:message_id>/read', methods=['POST'])
@admin_required
def admin_mark_read(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/messages/<int:message_id>/delete', methods=['POST'])
@admin_required
def admin_delete_message(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------------------------
# Seed data (runs once, only if the table is empty)
# ---------------------------------------------------------------------------
def seed_if_empty():
    if Listing.query.count() > 0:
        return
    seed = [
        dict(title='Deniz Manzaralı 3+1 Daire', city='mersin', city_label='Mersin, Yenişehir',
             region='tr', property_type='Daire', tier='orta', status='Satılık',
             price=4250000, currency='TRY', area_m2=145, rooms='3 Oda', floor_info='Kat 6'),
        dict(title='Sıfır, Havuzlu Villa', city='antalya', city_label='Antalya, Konyaaltı',
             region='tr', property_type='Villa', tier='ust', status='Satılık',
             price=8900000, currency='TRY', area_m2=220, rooms='4 Oda', floor_info='Müstakil'),
        dict(title='Yazlık, Site İçi Daire', city='bodrum', city_label='Bodrum, Yalıkavak',
             region='tr', property_type='Daire', tier='ust', status='Kiralık',
             price=6100000, currency='TRY', area_m2=95, rooms='2 Oda', floor_info='Kat 1'),
        dict(title='Şehir Merkezinde 2+1', city='istanbul', city_label='İstanbul, Kadıköy',
             region='tr', property_type='Daire', tier='orta', status='Satılık',
             price=5750000, currency='TRY', area_m2=110, rooms='2 Oda', floor_info='Kat 4'),
        dict(title='Deniz Manzaralı Villa', city='girne', city_label='Girne, Karaoğlanoğlu',
             region='kktc', property_type='Villa', tier='ust', status='Satılık',
             price=320000, currency='GBP', area_m2=210, rooms='4 Oda', floor_info='Müstakil'),
        dict(title='Merkezi Konumda Daire', city='lefkosa', city_label='Lefkoşa, Yenişehir',
             region='kktc', property_type='Daire', tier='eco', status='Kiralık',
             price=95000, currency='GBP', area_m2=90, rooms='2 Oda', floor_info='Kat 2'),
        dict(title='Sahil Sitesinde Daire', city='gazimagusa', city_label='Gazimağusa, Long Beach',
             region='kktc', property_type='Daire', tier='orta', status='Satılık',
             price=145000, currency='GBP', area_m2=75, rooms='1+1', floor_info='Kat 3'),
        dict(title='Yeni Proje, 1+1 Daire', city='iskele', city_label='İskele, Bafra',
             region='kktc', property_type='Daire', tier='eco', status='Yatırımlık',
             price=78000, currency='GBP', area_m2=65, rooms='1 Oda', floor_info='Kat 5'),
    ]
    for item in seed:
        db.session.add(Listing(**item))
    db.session.commit()
    print(f'Seed: {len(seed)} ilan eklendi.')


with app.app_context():
    db.create_all()
    seed_if_empty()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
