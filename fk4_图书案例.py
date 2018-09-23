from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# 设置数据库连接地址
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:mysql@127.0.0.1:3306/library"
# 是否追踪数据库修改  很消耗性能, 不建议使用
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# 设置在控制台显示底层执行的SQL语句
app.config["SQLALCHEMY_ECHO"] = False
# 设置秘钥
app.secret_key = 'looper'
# 创建数据库链接
db = SQLAlchemy(app)


# 创建作者表  一个作者对应多本书
class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 创建关系属性
    books = db.relationship('Book', backref='author')


# 创建图书表　　多
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 设置外键属性
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))


# 设置请求方式
@app.route('/', methods=['GET', 'POST'])
def index():
    # 根据请求方式判断返回的数据
    # 如果是GET方式
    if request.method == 'GET':
        # 查询数据库中的所有作者
        try:
            authors = Author.query.all()
        except Exception as e:
            flash('数据库异常')
            return redirect(url_for('index'))

        # 通过关联将所有的书和作者传到模板中，渲染到界面上
        return render_template('library.html', authors=authors)

    # 如果是POST方式
    # 获取客户端传回的参数
    author_name = request.form.get('author_name')
    book_name = request.form.get('book_name')

    # 校验参数，all([]) 列表中所有元素都有值才会返回true
    if not all([author_name, book_name]):
        # 存在无值的参数，提示参数不足
        flash('参数不足')
        return redirect(url_for('index'))

    # 判断书籍是否已存在，如果已存在，提示书籍已存在
    # 实质上是查询数据库中是否有名字==book_name的书
    book = Book.query.filter_by(name=book_name).first()
    if book:
        flash('该书籍已存在')
        return redirect(url_for('index'))

    # 判断是否有该作者
    author = Author.query.filter_by(name=author_name).first()
    # 增删改操作要设置回滚
    try:
        # 有作者
        if author:
            # 创建书籍对象
            book = Book(name=book_name)
            # 关联该作者
            author.books.append(book)
            # 添加到数据库中
            db.session.add(book)
            db.session.commit()

        else:
            # 没有作者，创建书籍和作者对象，关联作者和书籍，添加到数据库
            # 生成数据记录
            new_book = Book(name=book_name)
            new_author = Author(name=author_name)
            # 关联数据
            new_author.books.append(new_book)
            # 将数据记录提交到数据库
            db.session.add_all([new_book, new_author])
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(e)
        flash('数据库异常')
        return redirect(url_for('index'))

    return redirect(url_for('index'))

    # 增删改处理，失败后需要进行回滚


@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    # 删除书籍
    # 根据书籍id取出该书籍
    book = Book.query.get(book_id)
    # 将书籍从数据库删除
    db.session.delete(book)
    # 提交
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/delete_author/<int:author_id>')  # 传过来的路由变量是字符串类型，要转化为数字
def delete_author(author_id):
    # 删除作者
    # 根据作者id取出该作者
    author = Author.query.get(author_id)
    # 删除该作者关联的书籍和作者，删除一对多数据时，先删除多的一方，再删除一的一方
    # 删除作者的书籍
    for books in author.books:
        db.session.delete(books)
    # 删除作者
    db.session.delete(author)
    # 提交
    db.session.commit()

    return redirect(url_for('index'))



if __name__ == '__main__':
    db.drop_all()
    db.create_all()

    # 生成数据
    au1 = Author(name='老王')
    au2 = Author(name='老尹')
    au3 = Author(name='老刘')
    db.session.add_all([au1, au2, au3])
    db.session.commit()

    bk1 = Book(name='老王回忆录', author_id=au1.id)
    bk2 = Book(name='我读书少，你别骗我', author_id=au1.id)
    bk3 = Book(name='如何才能让自己更骚', author_id=au2.id)
    bk4 = Book(name='怎样征服美丽少女', author_id=au3.id)
    bk5 = Book(name='如何征服英俊少男', author_id=au3.id)
    db.session.add_all([bk1, bk2, bk3, bk4, bk5])
    db.session.commit()

    app.run(debug=True)
