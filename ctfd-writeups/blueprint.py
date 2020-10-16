import re
from collections import defaultdict
from CTFd.utils.decorators import admins_only, during_ctf_time_only, require_verified_emails, require_team, authed_only
from CTFd.utils.user import authed, get_current_user
from CTFd.utils import markdown
from flask import request, render_template, Blueprint, abort, redirect, url_for, send_from_directory
from CTFd.models import db, Challenges, Submissions, Solves, Pages
from .models import WriteUpChallenges

writeups_bp = Blueprint("writeups", __name__, template_folder="templates")


def load_bp(admin_route, base_route, plugin_dir='.'):
    @writeups_bp.route(f"{base_route}/assets/<path:path>", methods=["GET"])
    def assets(path: str):
        return send_from_directory(f"{plugin_dir}/assets", path)

    @writeups_bp.route(admin_route, methods=["POST"])
    @admins_only
    def update_config():
        form = request.form.to_dict()
        del form['nonce']

        challenges = defaultdict(lambda: {})

        for k, v in form.items():
            match = re.match(r'(?P<id>\d+)-(?P<prop>[a-zA-Z0-9-_]+)', k)
            if match:
                challenges[int(match.group('id'))][match.group('prop')] = v
            else:
                print(f"Unrecognized form key {k}")

        for challenge_id, props in challenges.items():
            challenge = Challenges.query.get(challenge_id)
            if 'accepting_wu' in props:
                if not challenge.writeup_challenge:
                    challenge.writeup_challenge = WriteUpChallenges(
                        name=f"Write-Up for {challenge.name}",
                        description='',
                        category='Write-Ups')
                challenge.writeup_challenge.value = props.get('wu_value', 5)
                challenge.writeup_challenge.solve_req = 'vis_before_solve' not in props
                submit_str = f"\n\n[Submit a write-up]({url_for('writeups.edit_writeup', challenge_id=challenge.id)}) for this challenge (+{challenge.writeup_challenge.value} pts.) or [view others']({url_for('writeups.writeups', challenge=challenge.id)}) write-ups."
                submit_re = r'\[Submit a write-up]\(.+\) for this challenge \(\+\d+ pts\.\) or \[view others\']\(.+\) write-ups\.'
                if not re.search(submit_re, challenge.description):
                    challenge.description += submit_str
                else:
                    challenge.description = re.sub(submit_re, submit_str, challenge.description)
            elif challenge.writeup_challenge:
                db.session.delete(challenge.writeup_challenge)

        db.session.commit()
        return get_config()

    @writeups_bp.route(admin_route, methods=["GET"])
    @admins_only
    def get_config():
        challenges = db.session.query(Challenges).filter(Challenges.type != 'writeup').all()

        rows = []
        for challenge in challenges:
            rows.append({
                'id': challenge.id,
                'name': challenge.name,
                'value': challenge.value,
                'accepting_wu': bool(challenge.writeup_challenge),
                'wu_value': challenge.writeup_challenge.value if challenge.writeup_challenge else 0,
                'solve_req': challenge.writeup_challenge.solve_req if challenge.writeup_challenge else True
            })

        return render_template("writeups_admin.html", challenges=rows)

    @writeups_bp.route(base_route, methods=["GET"])
    @during_ctf_time_only
    @authed_only
    def writeups():
        user = get_current_user()
        solves_ids = [s.challenge_id for s in user.team.solves]
        visible_writeups = (db.session.query(Submissions)
                            .filter(Submissions.challenge_id.in_(solves_ids))
                            .join(Challenges, Submissions.challenge_id == Challenges.id)
                            .filter(Challenges.type == 'writeup'))

        visible_writeups = visible_writeups.all()
        return render_template("writeups.html", writeups=visible_writeups)

    @writeups_bp.route(f"{base_route}/<int:writeup_id>", methods=["GET"])
    @during_ctf_time_only
    @authed_only
    def view_writeup(writeup_id: int):
        user = get_current_user()
        writeup = db.session.query(Submissions).get(writeup_id)
        error = {}
        content = ''
        editable = False

        if writeup.challenge.type != 'writeup':
            return redirect(url_for('writeups.writeups'))

        challenge = (db.session.query(Challenges)
                     .filter(Challenges.type != 'writeup')
                     .filter(Challenges.writeup_challenge == writeup.challenge)
                     .one_or_none())

        if not challenge or not challenge.writeup_challenge:
            return redirect(url_for('writeups.writeups'))

        solves = user.team.solves
        if not challenge.writeup_challenge.solve_req or challenge.id in (s.challenge_id for s in solves):
            content = markdown(writeup.provided)
            if writeup.user.id == user.id:
                editable = True
        else:
            error = {
                'heading': '403',
                'msg': 'Sorry, you must solve this challenge before viewing write-ups for it'
            }
        return render_template("view_writeup.html",
                               challenge=challenge,
                               content=content,
                               error=error,
                               user=user,
                               editable=editable)

    @writeups_bp.route(f"{base_route}/<int:challenge_id>/edit", methods=["GET", "POST"])
    @during_ctf_time_only
    @authed_only
    def edit_writeup(challenge_id: int):
        user = get_current_user()
        challenge = (db.session.query(Challenges)
                       .filter(Challenges.id == challenge_id)
                       .filter(Challenges.type != 'writeup')
                       .one_or_none())

        if not challenge or not challenge.writeup_challenge:
            return redirect(url_for('writeups.writeups'))

        writeup = next((s for s in user.solves if s.challenge_id == challenge.writeup_challenge.id), None)
        team_writeup = next((s for s in user.team.solves if s.challenge_id == challenge.writeup_challenge.id), None)
        if not writeup:
            writeup = Submissions(
                challenge=challenge.writeup_challenge,
                user=user,
                team=user.team,
                ip=request.remote_addr,
                provided='',
                type='incorrect' if team_writeup else 'correct'
            )
            db.session.add(writeup)

        if request.method == 'POST':
            writeup.provided = request.form.to_dict().get('content', '')
            db.session.commit()
            return redirect(url_for('writeups.view_writeup', writeup_id=writeup.id))
        elif request.method == 'GET':
            return render_template("edit_writeup.html", challenge=challenge, content=writeup.provided)

    # Add the Write-Ups page to pages so it appears in the nav bar
    if not db.session.query(Pages).filter(Pages.route == base_route).one_or_none():
        db.session.add(Pages(
            title='Write-Ups',
            route=base_route,
            content='',
            draft=False,
            hidden=False,
            auth_required=True
        ))
        db.session.commit()

    return writeups_bp
