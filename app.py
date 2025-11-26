from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite データベース
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///surgery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Surgery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)          # 手術日
    session = db.Column(db.String(2), nullable=False)  # 'AM' or 'PM'
    anesthesia = db.Column(db.String(10))              # '全' '局' など
    admission_date = db.Column(db.Date, nullable=True) # 入院日
    patient_id = db.Column(db.String(50))
    patient_name = db.Column(db.String(100))
    age_sex = db.Column(db.String(50))
    procedure = db.Column(db.String(200))
    surgeon = db.Column(db.String(100))
    note = db.Column(db.Text)

    def weekday_jp(self):
        # 0:月 … 6:日
        wk = ['月', '火', '水', '木', '金', '土', '日']
        return wk[self.date.weekday()]


def get_monday(d: date) -> date:
    """d を含む週の月曜日を返す"""
    return d - timedelta(days=d.weekday())


@app.before_first_request
def init_db():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def index():
    # データ登録（簡易）
    if request.method == 'POST':
        date_str = request.form['date']
        session = request.form['session']
        anesthesia = request.form['anesthesia']
        admission_str = request.form.get('admission_date') or None
        patient_id = request.form['patient_id']
        patient_name = request.form['patient_name']
        age_sex = request.form['age_sex']
        procedure = request.form['procedure']
        surgeon = request.form['surgeon']
        note = request.form['note']

        d = datetime.strptime(date_str, '%Y-%m-%d').date()
        admission_date = (
            datetime.strptime(admission_str, '%Y-%m-%d').date()
            if admission_str else None
        )

        s = Surgery(
            date=d,
            session=session,
            anesthesia=anesthesia,
            admission_date=admission_date,
            patient_id=patient_id,
            patient_name=patient_name,
            age_sex=age_sex,
            procedure=procedure,
            surgeon=surgeon,
            note=note,
        )
        db.session.add(s)
        db.session.commit()
        return redirect(url_for('index'))

    # ここからが「週表示」
    # ?start=YYYY-MM-DD があればその週、なければ「今日の週」
    start_str = request.args.get('start')
    if start_str:
        base_day = datetime.strptime(start_str, '%Y-%m-%d').date()
    else:
        base_day = date.today()

    monday = get_monday(base_day)
    tuesday = monday + timedelta(days=1)
    wednesday = monday + timedelta(days=2)
    friday = monday + timedelta(days=4)

    target_days = [monday, tuesday, wednesday, friday]

    # この週のデータをまとめて取得
    week_start = monday
    week_end = monday + timedelta(days=7)

    surgeries = (
        Surgery.query
        .filter(Surgery.date >= week_start, Surgery.date < week_end)
        .order_by(Surgery.date, Surgery.session)
        .all()
    )

    # 日付ごとにまとめる dict
    by_day = {d: [] for d in target_days}
    for s in surgeries:
        if s.date in by_day:
            by_day[s.date].append(s)

    return render_template(
        'week.html',
        monday=monday,
        tuesday=tuesday,
        wednesday=wednesday,
        friday=friday,
        by_day=by_day,
    )


if __name__ == '__main__':
    app.run(debug=True)