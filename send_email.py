from __future__ import print_function

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-billsend.json
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Bill Send'

"""Send an email message from the user's account.
"""

from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import httplib2
import base64
import os
import glob

from apiclient import errors
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
	import argparse

	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None


def send_message(service, user_id, message):
	"""Send an email message.

  Args:
	service: Authorized Gmail API service instance.
	user_id: User's email address. The special value "me"
	can be used to indicate the authenticated user.
	message: Message to be sent.

  Returns:
	Sent Message.
  """
	try:
		message = (service.users().messages().send(userId=user_id, body=message).execute())
		print('Message Id: %s' % message['id'])
		return message
	except errors.HttpError as error:
		print('An error occurred: %s' % error)


def create_message(sender, to, subject, message_text):
	"""Create a message for an email.

  Args:
	sender: Email address of the sender.
	to: Email address of the receiver.
	subject: The subject of the email message.
	message_text: The text of the email message.

  Returns:
	An object containing a base64url encoded email object.
  """
	message = MIMEText(message_text)
	message['to'] = to
	message['from'] = sender
	message['subject'] = subject
	return dict(raw=base64.urlsafe_b64encode(message.as_string()))


def create_message_with_attachment(sender, to, subject, message_text, file_dir,
								   filename):
	"""Create a message for an email.

  Args:
	sender: Email address of the sender.
	to: Email address of the receiver.
	subject: The subject of the email message.
	message_text: The text of the email message.
	file_dir: The directory containing the file to be attached.
	filename: The name of the file to be attached.

  Returns:
	An object containing a base64url encoded email object.
  """
	message = MIMEMultipart()
	message['to'] = to
	message['from'] = sender
	message['subject'] = subject

	msg = MIMEText(message_text)
	message.attach(msg)

	path = os.path.join(file_dir, filename)
	content_type, encoding = mimetypes.guess_type(path)

	if content_type is None or encoding is not None:
		content_type = 'application/octet-stream'
	main_type, sub_type = content_type.split('/', 1)
	if main_type == 'text':
		fp = open(path, 'rb')
		msg = MIMEText(fp.read(), _subtype=sub_type)
		fp.close()
	elif main_type == 'image':
		fp = open(path, 'rb')
		msg = MIMEImage(fp.read(), _subtype=sub_type)
		fp.close()
	elif main_type == 'audio':
		fp = open(path, 'rb')
		msg = MIMEAudio(fp.read(), _subtype=sub_type)
		fp.close()
	else:
		fp = open(path, 'rb')
		msg = MIMEBase(main_type, sub_type)
		msg.set_payload(fp.read())
		fp.close()

	msg.add_header('Content-Disposition', 'attachment', filename=filename)
	message.attach(msg)

	return {'raw': base64.urlsafe_b64encode(message.as_string())}


def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir, 'gmail-python-billsend.json')

	store = Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else:  # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def create_bill_message(to, filenames):
	base_dir = '/home/sangram/code/git/bill_sending/data/pdfs'
	email_body_text = open('email_message.txt', 'r').read()
	email_body_html = open('email_message.html', 'r').read()
	from_add = 'Property Manager <pm.aurumgrandechs@gmail.com>'
	email_subject = 'Adhoc Maintenance Bill | May 2017 | Aurum Grande Co-operative Housing Society Limited'

	message = MIMEMultipart('related')
	message['To'] = to
	message['From'] = from_add
	message['Subject'] = email_subject
	message.preamble = 'This is a multi-part message in MIME format.'

	msgAlternative = MIMEMultipart('alternative')
	message.attach(msgAlternative)

	msg = MIMEText(email_body_text)
	msgAlternative.attach(msg)

	msg = MIMEText(email_body_html, 'html')
	msgAlternative.attach(msg)

	for f in filenames:
		path = os.path.join(base_dir, os.path.basename(f))
		content_type, encoding = mimetypes.guess_type(path)

		if content_type is None or encoding is not None:
			content_type = 'application/octet-stream'
			
		main_type, sub_type = content_type.split('/', 1)
		fp = open(path, 'rb')
		msg = MIMEBase(main_type, sub_type)
		msg.set_payload(fp.read())
		fp.close()

		msg.add_header('Content-Disposition', 'attachment; filename="%s"' %(os.path.basename(f)))
		message.attach(msg)

	return {'raw': base64.urlsafe_b64encode(message.as_string())}

def main():
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('gmail', 'v1', http=http)

	f = open('data/may2017/email_addresses_owners_only.csv', 'r')
	#f = open('sample.csv', 'r')
	for line in f:
		line = line.rstrip()
		parts = line.split(',')
		apt_no = parts[1].replace(' ', '_', 1)
		bill_files = glob.glob('/home/sangram/code/git/bill_sending/data/pdfs/%s*.pdf' % (apt_no))
		to_add = parts[-1]
		if to_add != "" and len(bill_files) > 0:
			to_add = parts[2] + ' <' + to_add + '>'
			s = 'files:'
			for bill_f in bill_files:
				s = s + ' ' + os.path.basename(bill_f)
			s = s + ' and add: ' + to_add
			print (s)
			message = create_bill_message(to_add, bill_files)
			send_message(service, 'me', message)
		else:
			print ('some problem with add: #' + to_add + '# for ' + parts[1] + (' or no file found for attachment' if len(bill_files) == 0 else ''))
	f.close()

if __name__ == '__main__':
	main()
