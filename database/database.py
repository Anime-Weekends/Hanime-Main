import motor.motor_asyncio
from config import ADMINS, DB_URL, DB_NAME
from datetime import datetime, timedelta

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URL)
database = dbclient[DB_NAME]

user_data = database['users']
admin_data = database['admins']
link_data = database['links']

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        },
        'premium_status': {
            'is_premium': False,
            'expiry_date': None
        }
    }

# links functions
async def new_link(hash: str):
    return {
        'clicks' : 0,
        'hash': hash
    }

async def gen_new_count(hash: str):
    data = await new_link(hash)
    await link_data.insert_one(data)
    return

async def present_hash(hash:str):
    found = await(link_data.find_one({"hash" : hash}))
    return bool(found)

async def inc_count(hash: str):
    data = await link_data.find_one({'hash': hash})
    clicks = data.get('clicks')
    await link_data.update_one({'hash': hash}, {'$set': {'clicks': clicks+1}})
    return

async def get_clicks(hash: str):
    data = await link_data.find_one({'hash': hash})
    clicks = data.get('clicks')
    return clicks

# users functions
async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
    return

# admins functions
async def present_admin(user_id: int):
    found = await admin_data.find_one({'_id': user_id})
    return bool(found)

async def add_admin(user_id: int):
    user = new_user(user_id)
    await admin_data.insert_one(user)
    ADMINS.append(int(user_id))
    return

async def del_admin(user_id: int):
    await admin_data.delete_one({'_id': user_id})
    ADMINS.remove(int(user_id))
    return

async def full_adminbase():
    user_docs = admin_data.find()
    user_ids = [int(doc['_id']) async for doc in user_docs]
    return user_ids

# Premium functions
async def increasepremtime(user_id: int, time_for_prem: int):
    """
    This function updates the premium status and expiry date for the given user.
    The time_for_prem corresponds to how long the premium lasts.
    """
    # Retrieve the current user data
    user = await user_data.find_one({'_id': user_id})
    if user:
        premium_status = user.get('premium_status', {'is_premium': False, 'expiry_date': None})

        # Calculate the new premium expiry time based on the selection
        if time_for_prem == 1:
            new_expiry = datetime.now() + timedelta(days=7)
        elif time_for_prem == 2:
            new_expiry = datetime.now() + timedelta(days=30)
        elif time_for_prem == 3:
            new_expiry = datetime.now() + timedelta(days=90)
        elif time_for_prem == 4:
            new_expiry = datetime.now() + timedelta(days=180)
        elif time_for_prem == 5:
            new_expiry = datetime.now() + timedelta(days=365)

        # Update the premium status in the database
        await user_data.update_one(
            {'_id': user_id},
            {'$set': {'premium_status': {'is_premium': True, 'expiry_date': new_expiry}}}
        )
        return True
    return False
