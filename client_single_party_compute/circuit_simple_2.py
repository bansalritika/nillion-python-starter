from pdb import set_trace as bp
import argparse
import asyncio
import py_nillion_client as nillion
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers.nillion_client_helper import create_nillion_client
from helpers.nillion_keypath_helper import getUserKeyFromFile, getNodeKeyFromFile

load_dotenv()

# 1 Party running a simple circuit on 6 stored secrets and 3 compute time secrets
async def main():
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    userkey = getUserKeyFromFile(os.getenv("NILLION_USERKEY_PATH_PARTY_1"))
    nodekey = getNodeKeyFromFile(os.getenv("NILLION_NODEKEY_PATH_PARTY_1"))
    client = create_nillion_client(userkey, nodekey)
    party_id = client.party_id()
    user_id = client.user_id()

    program_id=f"{user_id}/circuit_simple_2"
    party_name="Party1"

    # Create a secret
    stored_secret = nillion.Secrets({
        "A": nillion.SecretInteger(3),
        "B": nillion.SecretInteger(14),
        "C": nillion.SecretInteger(5),
        "D": nillion.SecretInteger(6),
        "E": nillion.SecretInteger(2),
        "F": nillion.SecretInteger(1),
    })
    secret_bindings = nillion.ProgramBindings(program_id)
    secret_bindings.add_input_party(party_name, party_id)

    # Store a secret
    store_id = await client.store_secrets(
        cluster_id, secret_bindings, stored_secret, None
    )

    # Bind the parties in the computation to the client to set input and output parties
    compute_bindings = nillion.ProgramBindings(program_id)
    compute_bindings.add_input_party(party_name, party_id)
    compute_bindings.add_output_party(party_name, party_id)

    print(f"Computing using program {program_id}")
    print(f"Use secret store_id: {store_id}")

    computation_time_secrets = nillion.Secrets({
        "G": nillion.SecretInteger(9),
        "H": nillion.SecretInteger(10),
        "I": nillion.SecretInteger(7),
    })
    
    # Compute on the secrets
    compute_id = await client.compute(
        cluster_id,
        compute_bindings,
        [store_id],
        computation_time_secrets,
        nillion.PublicVariables({}),
    )

    # Print compute result
    print(f"The computation was sent to the network. compute_id: {compute_id}")
    while True:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"✅  Compute complete for compute_id {compute_event.uuid}")
            print(f"🖥️  The result is {compute_event.result.value}")
            break
    



    

asyncio.run(main())
