#   Global variables (defined in db_friends.py

#   User, Link, Post = db.auth_user, db.link, db.post
#   me, a0, a1 = auth.user_id, request.args(0), request.args(1)
#   myfriends = db(Link.source==me)(Link.accepted==True)
#   alphabetical = User.first_name|User.last_name
#   def name_of(user): return '%(first_name)s %(last_name)s' % user

import random

def index():
    if auth.user: redirect(URL('home'))
    else: redirect(URL('user/login'))
    return locals()

def user():
    return dict(form=auth())

def download():
    return response.download(request,db)

def confirmation():
    charges_url = URL('charges')
    vars = request.post_vars
    transactionID = request.args(0).split('?')
    db(db.post.id == transactionID[0]).update(paid=True)
    posted_by_name = name_of(db(db.post.id == transactionID[0]).select()[0].posted_by)
    post_body = (db(db.post.id == transactionID[0]).select()[0].body)
    post_amount = (db(db.post.id == transactionID[0]).select()[0].amount)
    return locals()

def call():
    session.forget()
    return service()

# our home page, will show our posts and posts by friends
@auth.requires_login()
def home():
    user = User(me)
    friendsList = db(Link.source == user)(Link.accepted == True).select()
    
    #myfriendlist = db(db.friendlist.me == user).select(db.friendlist.id)[0].id
    
    #if(myfriendlist == None):
    #    myfriendlist = db.friendlist.insert(me=user)

    #print(myfriendlist)

    #list of names of users for form to show the current user
    friendnames = []
    for name in friendsList:
        friendnames.append(name_of(name.target))

    print(friendnames)

    #list of IDs that will actually be passed to form
    friendIDs = []
    for friend in friendsList:
        friendIDs.append(friend.target)
    
    #db(db.friendlist.id == myfriendlist).update(friends=friendIDs)


    print(friendIDs)

    test = { }
    for i in range(len(friendnames)):
        test.update({friendIDs[i]:friendnames[i]})
    

    IS_IN_SET(test)

    #constraints for form
    Post.posted_by.default = me
    Post.posted_on.default = request.now
    #Post.posted_to.requires = IS_IN_DB(
    #               db(User), 
    #               User, 
    #               '%(first_name)s %(last_name)s', 
    #               multiple=True)
    Post.posted_to.requires = IS_IN_SET(test)
    Post.posted_to.format = '%(first_name)s %(last_name)s'
    Post.amount.default = '0.00'

    form = SQLFORM(Post, 
                   submit_button='Post Charge!',
                   formstyle='table3cols')

    form.vars.posted_to = IS_IN_SET(friendIDs)
    #friends = [me]+[row.target for row in myfriends.select(Link.target)]
    #posts = db(Post.posted_by.belongs(friends)).select(orderby=~Post.posted_on,limitby=(0,100))
    #posts = db(Post.posted_by==user.id).select(orderby=~Post.posted_on,limitby=(0,100))
    
    if form.process().accepted:
       response.flash = 'Charge posted!'
    elif form.errors:
       response.flash = 'Please correct errors'

    return locals()



# same as wall, except holds posted_to instead of posted_by
@auth.requires_login()
def charges():
    title = request.application
    #print(title)
    message = ''
    user = User(a0 or me)
    posts = db(Post.posted_to==user.id)(Post.paid==False).select(orderby=~Post.posted_on,limitby=(0,100))
    postcount = 0

    print(len(posts))

    if len(posts) == 0:
        message = 'You have no outstanding charges.'
    return locals()
"""
# a page for searching friends and requesting friendship
# not going to use this anymore, friends page will have search
# leave it here for reference
@auth.requires_login()
def search():
    currentuser = User(me)
    form = SQLFORM.factory(Field('name',requires=IS_NOT_EMPTY()))
    if form.accepts(request):
        tokens = form.vars.name.split()
        query = reduce(lambda a,b:a&b,
                       [User.first_name.contains(k)|User.last_name.contains(k) \
                            for k in tokens])
        people = db(query).select(orderby=alphabetical)
    else:
        people = []
    return locals()
"""

# a page for accepting and denying friendship requests
@auth.requires_login()
def friends():
    nofriends = ""
    friends = db(User.id==Link.source)(Link.target==me).select(orderby=alphabetical)
    if db(User.id==Link.source)(Link.target==me).count() == 0:
        nofriends = "you have no friends :("
    requests = db(User.id==Link.target)(Link.source==me).select(orderby=alphabetical)
    pendings = db(User.id==Link.target)(Link.source==me)(Link.accepted==False).select(orderby=alphabetical)
    
    #search page code
    currentuser = User(me)
    form = SQLFORM.factory(Field('name',requires=IS_NOT_EMPTY(),label=''))
    if form.accepts(request):
        tokens = form.vars.name.split()
        query = reduce(lambda a,b:a&b,
                       [User.first_name.contains(k)|User.last_name.contains(k) \
                            for k in tokens])
        people = db(query).select(orderby=alphabetical)
    else:
        people = []

    return locals()

# this is the Ajax callback
@auth.requires_login()
def friendship():
    """AJAX callback!"""
    if request.env.request_method!='POST': raise HTTP(400)
    if a0=='request' and not (Link(source=a1,target=me) or Link(source=me,target=a1) or Link(source=me,target=me)):
        # insert a new friendship request
        Link.insert(source=me,target=a1)
        #Link.insert(source=a1,target=me)
        
    elif a0=='accept':
        if not db(Link.source==me)(Link.target==a1).count():
            Link.insert(source=me,target=a1)
        # accept an existing friendship request
        db(Link.target==me)(Link.source==a1).update(accepted=True)
        db(Link.target==a1)(Link.source==me).update(accepted=True)
            
    elif a0=='deny':
        # deny an existing friendship request
        db(Link.target==me)(Link.source==a1).delete()
        db(Link.target==a1)(Link.source==me).delete()
        
    elif a0=='remove':
        # delete a previous friendship request
        db(Link.source==me)(Link.target==a1).delete()
        db(Link.source==a1)(Link.target==me).delete()
        
@auth.requires_login()
def payment():
    if request.env.request_method!='POST': raise HTTP(400)
    if a0=='paid':
        db(Post.id==a1).update(paid=True)
