import asyncio
import py_nillion_client as nillion
import os

from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv
from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey

# Load environment variables
home = os.getenv("HOME")
load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")

async def main():
    # 1. Initial setup
    # 1.1. Get cluster_id, grpc_endpoint, & chain_id from the .env file
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    grpc_endpoint = os.getenv("NILLION_NILCHAIN_GRPC")
    chain_id = os.getenv("NILLION_NILCHAIN_CHAIN_ID")
    
    # 1.2 Generate user and node keys from a seed
    seed = "my_new_seed"
    user_key = UserKey.from_seed(seed)
    node_key = NodeKey.from_seed(seed)

    # 2. Initialize NillionClient against nillion-devnet
    client = create_nillion_client(user_key, node_key)

    party_id = client.party_id
    user_id = client.user_id

    # 3. Pay for and store the program
    program_name = "secret_addition_complete"
    program_mir_path = f"../nada_quickstart_programs/target/{program_name}.nada.bin"

    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    private_key_hex = os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0")
    payments_wallet = LocalWallet(PrivateKey(bytes.fromhex(private_key_hex)), prefix="nillion")

    receipt_store_program = await get_quote_and_pay(
        client,
        nillion.Operation.store_program(program_mir_path),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    action_id = await client.store_program(
        cluster_id, program_name, program_mir_path, receipt_store_program
    )

    program_id = f"{user_id}/{program_name}"
    print("Stored program. action_id:", action_id)
    print("Stored program_id:", program_id)

    # 4. Create and store the first secret with permissions
    secret_value_1 = 500
    secret_1 = nillion.NadaValues({"my_int1": nillion.SecretInteger(secret_value_1)})

    party_name = "Party1"
    permissions = nillion.Permissions.default_for_user(client.user_id)
    permissions.add_compute_permissions({client.user_id: {program_id}})

    receipt_store_secret = await get_quote_and_pay(
        client,
        nillion.Operation.store_values(secret_1, ttl_days=5),
        payments_wallet,
        payments_client,
        cluster_id,
    )
    
    store_id_1 = await client.store_values(
        cluster_id, secret_1, permissions, receipt_store_secret
    )
    print(f"Stored secret with store_id: {store_id_1}")

    # 5. Create compute bindings, add a second secret, and run the computation
    compute_bindings = nillion.ProgramBindings(program_id)
    compute_bindings.add_input_party(party_name, party_id)
    compute_bindings.add_output_party(party_name, party_id)

    # Add the second secret for computation
    secret_value_2 = 20
    computation_time_secrets = nillion.NadaValues({"my_int2": nillion.SecretInteger(secret_value_2)})

    receipt_compute = await get_quote_and_pay(
        client,
        nillion.Operation.compute(program_id, computation_time_secrets),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    compute_id = await client.compute(
        cluster_id,
        compute_bindings,
        [store_id_1],
        computation_time_secrets,
        receipt_compute,
    )

    # Return the computation result
    print(f"The computation was sent to the network. compute_id: {compute_id}")
    while True:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"✅  Compute complete for compute_id {compute_event.uuid}")
            print(f"🖥️  The result is {compute_event.result.value}")
            return compute_event.result.value

if __name__ == "__main__":
    asyncio.run(main())
