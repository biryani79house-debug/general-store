from main import StoreSettings, SessionLocal, engine

# Create the table if it doesn't exist
StoreSettings.__table__.create(bind=engine, checkfirst=True)

# Create a session and check/add default settings
db = SessionLocal()
settings = db.query(StoreSettings).first()
if not settings:
    settings = StoreSettings()
    db.add(settings)
    db.commit()
    print('✅ Created default store settings')
else:
    print('✅ Store settings already exist')

# Print current settings
settings = db.query(StoreSettings).first()
print('Current settings:')
print(f'  store_name: {settings.store_name}')
print(f'  store_subtitle: {settings.store_subtitle}')
print(f'  store_location: {settings.store_location}')
print(f'  store_contact: {settings.store_contact}')
print(f'  delivery_note: {settings.delivery_note}')
db.close()
