import argparse
import json
import time
import logging
import os
from google.cloud import dialogflow
from dotenv import load_dotenv

logger = logging.getLogger('Logger')


def get_list_intents(project_id):
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)
    intents = intents_client.list_intents(request={"parent": parent})
    return intents


def delete_intent(project_id, intent_id):
    intents_client = dialogflow.IntentsClient()
    intent_path = intents_client.intent_path(project_id, intent_id)
    intents_client.delete_intent(request={"name": intent_path})


def create_intent(
        project_id, display_name, training_phrases_parts, message_texts
):
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)
    training_phrases = []
    for training_phrases_part in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(
            text=training_phrases_part
        )
        training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)
    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message]
    )
    response = intents_client.create_intent(
        request={"parent": parent, "intent": intent}
    )
    logger.debug("Intent created: {}".format(response))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug',
        type=bool,
        default=False,
        help='Turn DEBUG mode on'
    )
    parser.add_argument(
        '--add',
        type=bool,
        default=False,
        help='Only add intent'
    )
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='Intent from file'
    )
    arguments = parser.parse_args()

    level = logging.DEBUG if arguments.debug else logging.INFO
    logging.basicConfig(level=level)

    load_dotenv()
    dialogflow_project_id = os.environ['DIALOG-PROJECT-ID']
    base_qa_filename = arguments.file if arguments.file else os.environ['BASE_QA_FILENAME']

    input('''
          Renew DialogFlow base?
          press Enter to continue
          press Ctrl+C to Cancel
          ''')
    logging.debug('Renew DialogFlow base')

    if not os.path.exists(base_qa_filename):
        logging.debug(f'Something wrong with {base_qa_filename} file.')
        raise FileExistsError

    if not arguments.add:
        logging.debug(f'Delete all current intents')
        for intent in get_list_intents(dialogflow_project_id):
            if 'Default' in intent.display_name:
                continue
            delete_intent(dialogflow_project_id, intent.name.split('/')[-1])
            # limit 'All other requests per minute' of DialogFlow service
            time.sleep(3)

    with open(base_qa_filename, 'r') as file:
        questions = json.load(file)

    logging.debug(f'\nCreate intents from {base_qa_filename}\n')
    for phrase_part in questions:
        create_intent(
            dialogflow_project_id,
            phrase_part,
            questions[phrase_part]['questions'],
            questions[phrase_part]['answer']
        )
        # limit 'All other requests per minute' of DialogFlow service
        time.sleep(3)

    logging.debug('DialogFlow base update complete.')
