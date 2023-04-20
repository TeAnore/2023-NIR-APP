from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Task
from app.translate import translate


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    
    form = PostForm()
    if form.validate_on_submit():
        task = Task(author=current_user,
                    system = 'Web',
                    platform = '',
                    platform_type = '',
                    caption = '',
                    url = '',
                    video_key = '',
                    reaction = ''
        )

        db.session.add(task)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)

    tasks = current_user.created_tasks().paginate(page=page, per_page=current_app.config['TASKS_PER_PAGE'], error_out=False)

    next_url = url_for('main.index', page=tasks.next_num) if tasks.has_next else None
    prev_url = url_for('main.index', page=tasks.prev_num) if tasks.has_prev else None

    return render_template( 'index.html',
                            title=_('Home'),
                            form=form,
                            tasks=tasks.items,
                            next_url=next_url,
                            prev_url=prev_url
    )

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    tasks = Task.query.order_by(Task.created.desc()).paginate(
        page=page, per_page=current_app.config['TASKS_PER_PAGE'],
        error_out=False)
    next_url = url_for('main.explore', page=tasks.next_num) \
        if tasks.has_next else None
    prev_url = url_for('main.explore', page=tasks.prev_num) \
        if tasks.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           tasks=tasks.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    tasks = user.tasks.order_by(Task.created.desc()).paginate(
        page=page, per_page=current_app.config['TASKS_PER_PAGE'],
        error_out=False)
    next_url = url_for('main.user', username=user.username,
                       page=tasks.next_num) if tasks.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=tasks.prev_num) if tasks.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, tasks=tasks.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())
