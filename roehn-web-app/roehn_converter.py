# roehn_converter.py
import json
import csv
import uuid
import io
from datetime import datetime

class RoehnProjectConverter:
    def __init__(self):
        self.project_data = None
        self.modules_info = {
            'ADP-RL12': {'driver_guid': '80000000-0000-0000-0000-000000000006', 'slots': {'Load ON/OFF': 12}},
            'RL4': {'driver_guid': '80000000-0000-0000-0000-000000000010', 'slots': {'Load ON/OFF': 4}},
            'LX4': {'driver_guid': '80000000-0000-0000-0000-000000000003', 'slots': {'Shade': 4}},
            'SA1': {'driver_guid': '80000000-0000-0000-0000-000000000013', 'slots': {'IR': 1}},
            'DIM8': {'driver_guid': '80000000-0000-0000-0000-000000000001', 'slots': {'Load Dim': 8}}
        }

    def process_db_project(self, projeto):
        """Processa os dados do projeto do banco de dados para o formato Roehn"""
        print(f"Processando projeto: {projeto.nome}")
        print(f"Número de áreas: {len(projeto.areas)}")
        
        # Primeiro, criar todas as áreas e ambientes
        for area in projeto.areas:
            print(f"Processando área: {area.nome}")
            # Garantir que a área existe no projeto Roehn
            self._ensure_area_exists(area.nome)
            
            for ambiente in area.ambientes:
                print(f"Processando ambiente: {ambiente.nome}")
                # Garantir que o ambiente existe na área
                self._ensure_room_exists(area.nome, ambiente.nome)
        
        # Depois, garantir que todos os módulos existam
        for modulo in projeto.modulos:
            print(f"Processando módulo: {modulo.nome} ({modulo.tipo})")
            # Garantir que o módulo existe no projeto Roehn - USAR O NOME REAL
            self._ensure_module_exists(modulo.tipo, modulo.nome)  # Alteração aqui
        
        # Finalmente, processar os circuitos
        for area in projeto.areas:
            for ambiente in area.ambientes:
                for circuito in ambiente.circuitos:
                    print(f"Processando circuito: {circuito.identificador} ({circuito.tipo})")
                    
                    # Verificar se o circuito está vinculado
                    if circuito.vinculacao:
                        vinculacao = circuito.vinculacao
                        modulo = vinculacao.modulo
                        canal = vinculacao.canal
                        # USAR O NOME REAL DO MÓDULO EM VEZ DE GERAR UM
                        modulo_nome = modulo.nome  # Alteração aqui
                        
                        print(f"Circuito vinculado ao módulo: {modulo_nome}, canal: {canal}")
                        
                        try:
                            # Adicionar o circuito ao projeto Roehn
                            if circuito.tipo == 'luz':
                                guid = self._add_load(area.nome, ambiente.nome, circuito.nome or circuito.identificador)
                                self._link_load_to_module(guid, modulo_nome, canal)
                                print(f"Circuito de luz adicionado: {guid}")
                            elif circuito.tipo == 'persiana':
                                guid = self._add_shade(area.nome, ambiente.nome, circuito.nome or circuito.identificador)
                                self._link_shade_to_module(guid, modulo_nome, canal)
                                print(f"Circuito de persiana adicionado: {guid}")
                            elif circuito.tipo == 'hvac':
                                guid = self._add_hvac(area.nome, ambiente.nome, circuito.nome or circuito.identificador)
                                self._link_hvac_to_module(guid, modulo_nome, canal)
                                print(f"Circuito de HVAC adicionado: {guid}")
                        except Exception as e:
                            print(f"Erro ao processar circuito {circuito.id}: {e}")
                            # Continuar processando outros circuitos mesmo se um falhar
                            continue
                    else:
                        print(f"Circuito {circuito.id} não vinculado, ignorando.")

    def create_project(self, project_info):
        """Cria um projeto base compatível com o ROEHN Wizard"""
        project_guid = str(uuid.uuid4())
        now_iso = datetime.now().isoformat()
        
        # No método create_project, substitua a definição do m4_module por:

        # Módulo base M4 (obrigatório) com UnitComposers
        m4_module_guid = str(uuid.uuid4())
        m4_unit_composers = []

        # Lista de UnitComposers para o M4 baseada no exemplo do Roehn Wizard
        m4_composers_data = [
            {"Name": "Ativo", "PortNumber": 1, "PortType": 0, "IO": 0, "Kind": 0, "NotProgrammable": False},
            {"Name": "Modulos HSNET ativos", "PortNumber": 1, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Modulos HSNET registrados", "PortNumber": 2, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Data", "PortNumber": 3, "PortType": 600, "IO": 1, "Kind": 1, "NotProgrammable": True},
            {"Name": "Hora", "PortNumber": 4, "PortType": 600, "IO": 1, "Kind": 1, "NotProgrammable": True},
            {"Name": "DST", "PortNumber": 2, "PortType": 0, "IO": 0, "Kind": 0, "NotProgrammable": False},
            {"Name": "Nascer do Sol", "PortNumber": 5, "PortType": 600, "IO": 1, "Kind": 1, "NotProgrammable": True},
            {"Name": "Por do sol", "PortNumber": 6, "PortType": 600, "IO": 1, "Kind": 1, "NotProgrammable": True},
            {"Name": "Posição Solar", "PortNumber": 7, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Flag RTC", "PortNumber": 8, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Flag SNTP", "PortNumber": 9, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Flag MYIP", "PortNumber": 10, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Flag DDNS", "PortNumber": 11, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Web IP", "PortNumber": 1, "PortType": 1100, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Ultima inicializacao", "PortNumber": 2, "PortType": 1100, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Tensao", "PortNumber": 12, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Corrente", "PortNumber": 13, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Power", "PortNumber": 14, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
            {"Name": "Temperatura", "PortNumber": 15, "PortType": 600, "IO": 0, "Kind": 1, "NotProgrammable": False},
        ]

        # Iniciar IDs a partir de 39, conforme o exemplo
        next_unit_id = 39

        for composer in m4_composers_data:
            unit_composer = {
                "$type": "UnitComposer",
                "Name": composer["Name"],
                "PortNumber": composer["PortNumber"],
                "PortType": composer["PortType"],
                "IO": composer["IO"],
                "Kind": composer["Kind"],
                "NotProgrammable": composer["NotProgrammable"],
                "Unit": {
                    "$type": "Unit",
                    "Id": next_unit_id,
                    "Event": 0,
                    "Scene": 0,
                    "Disabled": False,
                    "Logged": False,
                    "Memo": False,
                    "Increment": False
                },
                "Value": 0
            }
            m4_unit_composers.append(unit_composer)
            next_unit_id += 1

        m4_module = {
            "$type": "Module",
            "Name": "AQL-GV-M4",
            "DriverGuid": "80000000-0000-0000-0000-000000000016",
            "Guid": m4_module_guid,
            "IpAddress": project_info.get('m4_ip'),
            "HsnetAddress": int(project_info.get('m4_hsnet', 245)),
            "PollTiming": 0,
            "Disabled": False,
            "RemotePort": 0,
            "RemoteIpAddress": None,
            "Notes": None,
            "Logicserver": True,
            "DevID": int(project_info.get('m4_devid', 1)),
            "DevIDSlave": 0,
            "UnitComposers": m4_unit_composers,  # Adicionando os UnitComposers
            "Slots": [
                {
                    "$type": "Slot",
                    "SlotCapacity": 24,
                    "SlotType": 0,
                    "InitialPort": 1,
                    "IO": 0,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"],
                    "Name": "ACNET",
                },
                {
                    "$type": "Slot",
                    "SlotCapacity": 96,
                    "SlotType": 8,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"] * 96,
                    "Name": "Scene",
                },
            ],
            "SmartGroup": 1,
            "UserInterfaceGuid": "00000000-0000-0000-0000-000000000000",
            "PIRSensorReportEnable": False,
            "PIRSensorReportID": 0,
        }

        # SpecialActions padrão
        def default_special_actions():
            return [
                {"$type": "SpecialAction", "Name": "All HVAC",  "Guid": str(uuid.uuid4()), "Type": 4},
                {"$type": "SpecialAction", "Name": "All Lights","Guid": str(uuid.uuid4()), "Type": 2},
                {"$type": "SpecialAction", "Name": "All Shades","Guid": str(uuid.uuid4()), "Type": 3},
                {"$type": "SpecialAction", "Name": "OFF",       "Guid": str(uuid.uuid4()), "Type": 0},
                {"$type": "SpecialAction", "Name": "Volume",    "Guid": str(uuid.uuid4()), "Type": 1},
            ]

        startup_var = {
            "$type": "Variable",
            "Name": "Startup",
            "Description": "This variable indicates that the system has just been booted.",
            "Guid": str(uuid.uuid4()),
            "Configurable": False,
            "Memorizable": False,
            "IsStartup": True,
            "AllowsModify": False,
            "VariableType": 0,
            "NumericSubType": 0,
            "InitialValue": 0,
            "Id": 1,
        }

        # Montagem do projeto
        self.project_data = {
            "$type": "Project",
            "Areas": [
                {
                    "$type": "Area",
                    "Scenes": [],
                    "Scripts": [],
                    "Variables": [],
                    "SpecialActions": default_special_actions(),
                    "Guid": str(uuid.uuid4()),
                    "Name": project_info.get('tech_area', 'Área Técnica'),
                    "Notes": "",
                    "NotDisplayOnROEHNApp": False,
                    "SubItems": [
                        {
                            "$type": "Room",
                            "NotDisplayOnROEHNApp": False,
                            "Name": project_info.get('tech_room', 'Sala Técnica'),
                            "Notes": None,
                            "Scenes": [],
                            "Scripts": [],
                            "Variables": [],
                            "LoadOutputs": [],
                            "UserInterfaces": [],
                            "AutomationBoards": [
                                {
                                    "$type": "AutomationBoard",
                                    "Name": project_info.get('board_name', 'Quadro Elétrico'),
                                    "Notes": None,
                                    "ModulesList": [m4_module],
                                }
                            ],
                            "SpecialActions": default_special_actions(),
                            "Guid": str(uuid.uuid4()),
                        }
                    ],
                }
            ],
            "Scenes": [],
            "Scripts": [],
            "Variables": [startup_var],
            "SpecialActions": default_special_actions(),
            "SavedProfiles": None,
            "SavedControlModels": None,
            "ClientInfo": {
                "$type": "ClientInfo",
                "Name": project_info.get('client_name', 'Cliente'),
                "Email": project_info.get('client_email', ''),
                "Phone": project_info.get('client_phone', ''),
            },
            "Name": project_info.get('project_name', 'Novo Projeto'),
            "Path": None,
            "Guid": project_guid,
            "Created": now_iso,
            "LastModified": now_iso,
            "LastUpload": None,
            "LastTimeSaved": now_iso,
            "ProgrammerInfo": {
                "$type": "ProgrammerInfo",
                "Name": project_info.get('programmer_name', 'Programador'),
                "Email": project_info.get('programmer_email', ''),
                "Guid": project_info.get('programmer_guid', str(uuid.uuid4())),
            },
            "CloudConfig": {
                "$type": "CloudConfig",
                "CloudHomesystemsId": 0,
                "CloudSerialNumber": 0,
                "RemoteAcess": False,
                "CloudConfiguration": None,
                "CloudLocalName": None,
                "CloudPassword": None,
            },
            "ProjectSchemaVersion": 1,
            "SoftwareVersion": project_info.get('software_version', '1.0.8.67'),
            "SelectedTimeZoneID": project_info.get('timezone_id', 'America/Bahia'),
            "Latitude": float(project_info.get('lat', 0.0)),
            "Longitude": float(project_info.get('lon', 0.0)),
            "Notes": None,
            "RoehnAppExport": False,
        }
        
        return self.project_data

    def process_csv(self, csv_content):
        """Processa o conteúdo CSV e adiciona os circuitos ao projeto"""
        if not self.project_data:
            raise ValueError("Projeto não inicializado. Chame create_project primeiro.")
        
        # Converter conteúdo CSV para lista de dicionários
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        shades_seen = set()
        
        for row in reader:
            circuito = (row.get("Circuito") or "").strip()
            tipo = (row.get("Tipo") or "").strip().lower()
            nome = (row.get("Nome") or "").strip()
            area = (row.get("Area") or "").strip()
            ambiente = (row.get("Ambiente") or "").strip()
            canal = (row.get("Canal") or "").strip()
            modulo = (row.get("Modulo") or "").strip()
            id_modulo = (row.get("id Modulo") or row.get("id_modulo") or "").strip()

            if not area or not ambiente or not modulo or not id_modulo or not canal:
                continue
                
            try:
                canal = int(canal)
            except ValueError:
                continue

            self._ensure_area_exists(area)
            self._ensure_room_exists(area, ambiente)
            # Para CSV, ainda usamos o formato antigo para compatibilidade
            modulo_nome = self._ensure_module_exists(modulo, f"{modulo}_{id_modulo}")

            if tipo == "luz":
                guid = self._add_load(area, ambiente, nome or circuito or "Load")
                self._link_load_to_module(guid, modulo_nome, canal)
            elif tipo == "persiana":
                key = f"{area}|{ambiente}|{nome or circuito or 'Persiana'}"
                if key not in shades_seen:
                    guid = self._add_shade(area, ambiente, nome or circuito or "Persiana")
                    self._link_shade_to_module(guid, modulo_nome, canal)
                    shades_seen.add(key)
            elif tipo == "hvac":
                guid = self._add_hvac(area, ambiente, nome or "Ar-Condicionado")
                self._link_hvac_to_module(guid, modulo_nome, canal)
        
        return self.project_data

    def _ensure_area_exists(self, area_name):
        """Garante que uma área existe no projeto Roehn"""
        for area in self.project_data["Areas"]:
            if area["Name"] == area_name:
                return area
        
        # Se a área não existe, cria uma nova
        new_area = {
            "$type": "Area",
            "Scenes": [],
            "Scripts": [],
            "Variables": [],
            "SpecialActions": [
                {"$type": "SpecialAction", "Name": "All HVAC", "Guid": str(uuid.uuid4()), "Type": 4},
                {"$type": "SpecialAction", "Name": "All Lights", "Guid": str(uuid.uuid4()), "Type": 2},
                {"$type": "SpecialAction", "Name": "All Shades", "Guid": str(uuid.uuid4()), "Type": 3},
                {"$type": "SpecialAction", "Name": "OFF", "Guid": str(uuid.uuid4()), "Type": 0},
                {"$type": "SpecialAction", "Name": "Volume", "Guid": str(uuid.uuid4()), "Type": 1}
            ],
            "Guid": str(uuid.uuid4()),
            "Name": area_name,
            "Notes": "",
            "NotDisplayOnROEHNApp": False,
            "SubItems": []
        }
        self.project_data["Areas"].append(new_area)
        return new_area

    def _ensure_room_exists(self, area_name, room_name):
        """Garante que um ambiente existe em uma área"""
        area = self._ensure_area_exists(area_name)
        
        for room in area["SubItems"]:
            if room["Name"] == room_name:
                return room
        
        # Se o ambiente não existe, cria um novo
        new_room = {
            "$type": "Room",
            "NotDisplayOnROEHNApp": False,
            "Name": room_name,
            "Notes": None,
            "Scenes": [],
            "Scripts": [],
            "Variables": [],
            "LoadOutputs": [],
            "UserInterfaces": [],
            "AutomationBoards": [],
            "SpecialActions": [
                {"$type": "SpecialAction", "Name": "All HVAC", "Guid": str(uuid.uuid4()), "Type": 4},
                {"$type": "SpecialAction", "Name": "All Lights", "Guid": str(uuid.uuid4()), "Type": 2},
                {"$type": "SpecialAction", "Name": "All Shades", "Guid": str(uuid.uuid4()), "Type": 3},
                {"$type": "SpecialAction", "Name": "OFF", "Guid": str(uuid.uuid4()), "Type": 0},
                {"$type": "SpecialAction", "Name": "Volume", "Guid": str(uuid.uuid4()), "Type": 1}
            ],
            "Guid": str(uuid.uuid4())
        }
        area["SubItems"].append(new_room)
        return new_room

    def _ensure_module_exists(self, model, module_name):
        """Garantir que um módulo existe no projeto usando o nome real"""
        modules_list = self.project_data["Areas"][0]["SubItems"][0]["AutomationBoards"][0]["ModulesList"]
        
        # Verificar se o módulo já existe pelo nome
        for module in modules_list:
            if module["Name"] == module_name:
                return module_name
                
        # Criar novo módulo se não existir
        hsnet = self._find_max_hsnet() + 1
        while self._is_hsnet_duplicate(hsnet):
            hsnet += 1
            
        dev_id = self._find_max_dev_id() + 1
        
        # Determinar o tipo de módulo e criar
        u = model.upper()
        if "RL12" in u:
            self._create_rl12_module(module_name, hsnet, dev_id)
        elif "RL4" in u:
            self._create_rl4_module(module_name, hsnet, dev_id)
        elif "LX4" in u:
            self._create_lx4_module(module_name, hsnet, dev_id)
        elif "SA1" in u:
            self._create_sa1_module(module_name, hsnet, dev_id)
        elif "DIM8" in u or "ADP-DIM8" in u:
            self._create_dim8_module(module_name, hsnet, dev_id)
            
        return module_name

    def _create_rl4_module(self, name, hsnet_address, dev_id):
        """Cria um módulo RL4"""
        new_module_guid = str(uuid.uuid4())
        new_module = {
            "$type": "Module",
            "Name": name,
            "DriverGuid": "80000000-0000-0000-0000-000000000010",
            "Guid": new_module_guid,
            "IpAddress": "",
            "HsnetAddress": hsnet_address,
            "PollTiming": 0,
            "Disabled": False,
            "RemotePort": 0,
            "RemoteIpAddress": "",
            "Notes": None,
            "Logicserver": False,
            "DevID": dev_id,
            "DevIDSlave": 0,
            "UnitComposers": None,
            "Slots": [
                {
                    "$type": "Slot",
                    "SlotCapacity": 4,
                    "SlotType": 1,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"] * 4,
                    "Name": "Load ON/OFF"
                }
            ],
            "SmartGroup": 1,
            "UserInterfaceGuid": "00000000-0000-0000-0000-000000000000",
            "PIRSensorReportEnable": False,
            "PIRSensorReportID": 0
        }
        self._add_module_to_project(new_module, new_module_guid)

    def _create_lx4_module(self, name, hsnet_address, dev_id):
        """Cria um módulo LX4"""
        next_unit_id = self._find_max_unit_id() + 1
        unit_composers = []
        for i in range(4):
            for j in range(4):
                unit_composers.append({
                    "$type": "UnitComposer",
                    "Name": f"Opening Percentage {i+1} {j+1}",
                    "Unit": {
                        "$type": "Unit",
                        "Id": next_unit_id,
                        "Event": 0,
                        "Scene": 0,
                        "Disabled": False,
                        "Logged": False,
                        "Memo": False,
                        "Increment": False
                    },
                    "PortNumber": 1 if j % 2 == 0 else 5,
                    "PortType": 6,
                    "NotProgrammable": False,
                    "Kind": 1,
                    "IO": 1 if j % 2 == 0 else 0,
                    "Value": 0
                })
                next_unit_id += 1

        new_module_guid = str(uuid.uuid4())
        new_module = {
            "$type": "Module",
            "Name": name,
            "DriverGuid": "80000000-0000-0000-0000-000000000003",
            "Guid": new_module_guid,
            "IpAddress": "",
            "HsnetAddress": hsnet_address,
            "PollTiming": 0,
            "Disabled": False,
            "RemotePort": 0,
            "RemoteIpAddress": "",
            "Notes": None,
            "Logicserver": False,
            "DevID": dev_id,
            "DevIDSlave": 0,
            "UnitComposers": unit_composers,
            "Slots": [
                {
                    "$type": "Slot",
                    "SlotCapacity": 4,
                    "SlotType": 7,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"] * 4,
                    "Name": "Shade"
                },
                {
                    "$type": "Slot",
                    "SlotCapacity": 6,
                    "SlotType": 6,
                    "InitialPort": 1,
                    "IO": 0,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"] * 6,
                    "Name": "PNET"
                }
            ],
            "SmartGroup": 1,
            "UserInterfaceGuid": "00000000-0000-0000-0000-000000000000",
            "PIRSensorReportEnable": False,
            "PIRSensorReportID": 0
        }
        self._add_module_to_project(new_module, new_module_guid)

    def _create_sa1_module(self, name, hsnet_address, dev_id):
        """Cria um módulo SA1"""
        next_unit_id = self._find_max_unit_id() + 1
        unit_composers = []
        composers_data = [
            {"Name": "Power", "PortNumber": 1, "PortType": 600, "NotProgrammable": False, "Kind": 1, "IO": 1},
            {"Name": "Mode", "PortNumber": 2, "PortType": 600, "NotProgrammable": False, "Kind": 1, "IO": 1},
            {"Name": "Fan Speed", "PortNumber": 4, "PortType": 600, "NotProgrammable": False, "Kind": 1, "IO": 1},
            {"Name": "Swing", "PortNumber": 5, "PortType": 600, "NotProgrammable": False, "Kind": 1, "IO": 1},
            {"Name": "Temp Up", "PortNumber": 11, "PortType": 600, "NotProgrammable": False, "Kind": 1, "IO": 1},
            {"Name": "Temp Down", "PortNumber": 12, "PortType": 600, "NotProgrammable": False, "Kind": 1, "IO": 1},
            {"Name": "Display/Light", "PortNumber": 3, "PortType": 100, "NotProgrammable": False, "Kind": 0, "IO": 1},
        ]
        for composer in composers_data:
            unit_composers.append({
                "$type": "UnitComposer",
                "Name": composer["Name"],
                "Unit": {
                    "$type": "Unit",
                    "Id": next_unit_id,
                    "Event": 0,
                    "Scene": 0,
                    "Disabled": False,
                    "Logged": False,
                    "Memo": False,
                    "Increment": False
                },
                "PortNumber": composer["PortNumber"],
                "PortType": composer["PortType"],
                "NotProgrammable": composer["NotProgrammable"],
                "Kind": composer["Kind"],
                "IO": composer["IO"],
                "Value": 0
            })
            next_unit_id += 1

        new_module_guid = str(uuid.uuid4())
        new_module = {
            "$type": "ModuleHVAC",
            "SubItemComposers": [unit_composers],
            "GTWItemComposers": [],
            "Name": name,
            "DriverGuid": "80000000-0000-0000-0000-000000000013",
            "Guid": new_module_guid,
            "IpAddress": "",
            "HsnetAddress": hsnet_address,
            "PollTiming": 0,
            "Disabled": False,
            "RemotePort": 0,
            "RemoteIpAddress": "",
            "Notes": None,
            "Logicserver": False,
            "DevID": dev_id,
            "DevIDSlave": 0,
            "Slots": [
                {
                    "$type": "Slot",
                    "SlotCapacity": 1,
                    "SlotType": 4,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"],
                    "Name": "IR"
                }
            ],
            "SmartGroup": 1,
            "UserInterfaceGuid": "00000000-0000-0000-0000-000000000000",
            "PIRSensorReportEnable": False,
            "PIRSensorReportID": 0
        }

        self._add_module_to_project(new_module, new_module_guid)

    def _create_dim8_module(self, name, hsnet_address, dev_id):
        """Cria um módulo DIM8"""
        new_module_guid = str(uuid.uuid4())
        zero = "00000000-0000-0000-0000-000000000000"

        new_module = {
            "$type": "Module",
            "Name": name,
            "DriverGuid": "80000000-0000-0000-0000-000000000001",
            "Guid": new_module_guid,
            "IpAddress": "",
            "HsnetAddress": hsnet_address,
            "PollTiming": 0,
            "Disabled": False,
            "RemotePort": 0,
            "RemoteIpAddress": "",
            "Notes": None,
            "Logicserver": False,
            "DevID": dev_id,
            "DevIDSlave": 0,
            "UnitComposers": None,
            "Slots": [
                {
                    "$type": "Slot",
                    "SlotCapacity": 8,
                    "SlotType": 2,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": [zero] * 8,
                    "Name": "Load Dim"
                },
                {
                    "$type": "Slot",
                    "SlotCapacity": 6,
                    "SlotType": 6,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": [zero] * 6,
                    "Name": "PNET"
                }
            ],
            "SmartGroup": 1,
            "UserInterfaceGuid": "00000000-0000-0000-0000-000000000000",
            "PIRSensorReportEnable": False,
            "PIRSensorReportID": 0
        }

        self._add_module_to_project(new_module, new_module_guid)

    def _create_rl12_module(self, name, hsnet_address, dev_id):
        """Cria um módulo RL12"""
        new_module_guid = str(uuid.uuid4())
        new_module = {
            "$type": "Module",
            "Name": name,
            "DriverGuid": "80000000-0000-0000-0000-000000000006",
            "Guid": new_module_guid,
            "IpAddress": "",
            "HsnetAddress": hsnet_address,
            "PollTiming": 0,
            "Disabled": False,
            "RemotePort": 0,
            "RemoteIpAddress": "",
            "Notes": None,
            "Logicserver": False,
            "DevID": dev_id,
            "DevIDSlave": 0,
            "UnitComposers": None,
            "Slots": [
                {
                    "$type": "Slot",
                    "SlotCapacity": 12,
                    "SlotType": 1,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"] * 12,
                    "Name": "Load ON/OFF"
                },
                {
                    "$type": "Slot",
                    "SlotCapacity": 6,
                    "SlotType": 6,
                    "InitialPort": 1,
                    "IO": 1,
                    "UnitComposers": None,
                    "SubItemsGuid": ["00000000-0000-0000-0000-000000000000"] * 6,
                    "Name": "PNET"
                }
            ],
            "SmartGroup": 1,
            "UserInterfaceGuid": "00000000-0000-0000-0000-000000000000",
            "PIRSensorReportEnable": False,
            "PIRSensorReportID": 0
        }
        self._add_module_to_project(new_module, new_module_guid)

    # Implementar métodos similares para outros tipos de módulos:
    # _create_rl4_module, _create_lx4_module, _create_sa1_module, _create_dim8_module

    def _add_module_to_project(self, new_module, new_module_guid):
        """Adiciona um módulo ao projeto e atualiza o ACNET"""
        modules_list = self.project_data["Areas"][0]["SubItems"][0]["AutomationBoards"][0]["ModulesList"]
        modules_list.append(new_module)

        # Atualizar o ACNET do módulo M4
        if modules_list:
            first_module = modules_list[0]  # O M4 é o primeiro módulo
            for slot in first_module.get("Slots", []):
                if slot.get("Name") == "ACNET":
                    # Encontrar a primeira posição vazia e substituir pelo novo GUID
                    for i, guid in enumerate(slot["SubItemsGuid"]):
                        if guid == "00000000-0000-0000-0000-000000000000":
                            slot["SubItemsGuid"][i] = new_module_guid
                            break
                    else:
                        # Se não encontrou posição vazia, adiciona ao final
                        slot["SubItemsGuid"].append(new_module_guid)
                    
                    # Garantir que há pelo menos um item vazio no final
                    if slot["SubItemsGuid"][-1] != "00000000-0000-0000-0000-000000000000":
                        slot["SubItemsGuid"].append("00000000-0000-0000-0000-000000000000")
                    
                    break

    def _find_max_dev_id(self):
        """Encontra o maior DevID atual"""
        max_id = 0
        if not self.project_data:
            return max_id
            
        try:
            modules = self.project_data['Areas'][0]['SubItems'][0]['AutomationBoards'][0]['ModulesList']
            for module in modules:
                if 'DevID' in module and module['DevID'] > max_id:
                    max_id = module['DevID']
        except (KeyError, IndexError):
            pass
            
        return max_id

    def _find_max_hsnet(self):
        """Encontra o maior HSNET atual"""
        max_addr = 100
        if not self.project_data:
            return max_addr
            
        try:
            modules = self.project_data['Areas'][0]['SubItems'][0]['AutomationBoards'][0]['ModulesList']
            for module in modules:
                if 'HsnetAddress' in module and module['HsnetAddress'] > max_addr:
                    max_addr = module['HsnetAddress']
        except (KeyError, IndexError):
            pass
            
        return max_addr

    def _is_hsnet_duplicate(self, hsnet_address):
        """Verifica se um endereço HSNET já está em uso"""
        if not self.project_data:
            return False
            
        try:
            modules = self.project_data['Areas'][0]['SubItems'][0]['AutomationBoards'][0]['ModulesList']
            for module in modules:
                if 'HsnetAddress' in module and module['HsnetAddress'] == hsnet_address:
                    return True
        except (KeyError, IndexError):
            pass
            
        return False

    def _add_shade(self, area, ambiente, name, description="Persiana"):
        """Adiciona uma persiana ao projeto"""
        area_idx = next(i for i, a in enumerate(self.project_data["Areas"]) if a["Name"] == area)
        room_idx = next(i for i, r in enumerate(self.project_data["Areas"][area_idx]["SubItems"]) if r["Name"] == ambiente)

        next_unit_id = self._find_max_unit_id() + 1

        new_shade = {
            "$type": "Shade",
            "ShadeType": 0,
            "ShadeIcon": 0,
            "ProfileGuid": "20000000-0000-0000-0000-000000000001",
            "UnitMovement": {
                "$type": "Unit",
                "Id": next_unit_id,
                "Event": 0,
                "Scene": 0,
                "Disabled": False,
                "Logged": False,
                "Memo": False,
                "Increment": False
            },
            "UnitOpenedPercentage": {
                "$type": "Unit",
                "Id": next_unit_id + 1,
                "Event": 0,
                "Scene": 0,
                "Disabled": False,
                "Logged": False,
                "Memo": False,
                "Increment": False
            },
            "UnitCurrentPosition": {
                "$type": "Unit",
                "Id": next_unit_id + 2,
                "Event": 0,
                "Scene": 0,
                "Disabled": False,
                "Logged": False,
                "Memo": False,
                "Increment": False
            },
            "Name": name,
            "Guid": str(uuid.uuid4()),
            "Description": description
        }
        self.project_data["Areas"][area_idx]["SubItems"][room_idx]["LoadOutputs"].append(new_shade)
        return new_shade["Guid"]

    def _add_hvac(self, area, ambiente, name, description="HVAC"):
        """Adiciona um HVAC ao projeto"""
        area_idx = next(i for i, a in enumerate(self.project_data["Areas"]) if a["Name"] == area)
        room_idx = next(i for i, r in enumerate(self.project_data["Areas"][area_idx]["SubItems"]) if r["Name"] == ambiente)

        new_hvac = {
            "$type": "HVAC",
            "ProfileGuid": "14000000-0000-0000-0000-000000000001",
            "ControlModelGuid": "17000000-0000-0000-0000-000000000001",
            "Unit": None,
            "Name": name,
            "Guid": str(uuid.uuid4()),
            "Description": description
        }

        self.project_data["Areas"][area_idx]["SubItems"][room_idx]["LoadOutputs"].append(new_hvac)
        return new_hvac["Guid"]

    def _link_shade_to_module(self, shade_guid, module_name, canal):
        """Vincula uma persiana a um módulo"""
        try:
            modules_list = self.project_data['Areas'][0]['SubItems'][0]['AutomationBoards'][0]['ModulesList']
            for module in modules_list:
                if module['Name'] == module_name:
                    for slot in module['Slots']:
                        if slot['Name'] == 'Shade':
                            while len(slot['SubItemsGuid']) < slot['SlotCapacity']:
                                slot['SubItemsGuid'].append("00000000-0000-0000-0000-000000000000")
                            slot['SubItemsGuid'][canal-1] = shade_guid
                            return True
        except Exception as e:
            print("Erro ao linkar persiana:", e)
        return False

    def _link_hvac_to_module(self, hvac_guid, module_name, canal):
        """Vincula um HVAC a um módulo"""
        try:
            modules_list = self.project_data['Areas'][0]['SubItems'][0]['AutomationBoards'][0]['ModulesList']
            for module in modules_list:
                if module['Name'] == module_name:
                    for slot in module['Slots']:
                        if slot['Name'] == 'IR':
                            while len(slot['SubItemsGuid']) < slot['SlotCapacity']:
                                slot['SubItemsGuid'].append("00000000-0000-0000-0000-000000000000")
                            slot['SubItemsGuid'][canal-1] = hvac_guid
                            return True
        except Exception as e:
            print("Erro ao linkar HVAC:", e)
        return False

    def _add_load(self, area, ambiente, name, power=0.0, description="ON/OFF"):
        """Adiciona um circuito de iluminação"""
        area_idx = next(i for i, a in enumerate(self.project_data["Areas"]) if a["Name"] == area)
        room_idx = next(i for i, r in enumerate(self.project_data["Areas"][area_idx]["SubItems"]) if r["Name"] == ambiente)

        next_unit_id = self._find_max_unit_id() + 1

        new_load = {
            "$type": "Circuit",
            "LoadType": 0,
            "IconPath": 0,
            "Power": power,
            "ProfileGuid": "10000000-0000-0000-0000-000000000001",
            "Unit": {
                "$type": "Unit",
                "Id": next_unit_id,
                "Event": 0,
                "Scene": 0,
                "Disabled": False,
                "Logged": False,
                "Memo": False,
                "Increment": False
            },
            "Name": name,
            "Guid": str(uuid.uuid4()),
            "Description": description
        }
        self.project_data["Areas"][area_idx]["SubItems"][room_idx]["LoadOutputs"].append(new_load)
        return new_load["Guid"]

    def _find_max_unit_id(self):
        """Encontra o maior Unit ID atual, considerando UnitComposers"""
        max_id = 0
        
        def find_ids(data):
            nonlocal max_id
            if isinstance(data, dict):
                if data.get("$type") == "Unit" and "Id" in data:
                    max_id = max(max_id, data["Id"])
                # Também procurar em UnitComposers
                if "UnitComposers" in data and isinstance(data["UnitComposers"], list):
                    for composer in data["UnitComposers"]:
                        if isinstance(composer, dict) and "Unit" in composer:
                            unit = composer["Unit"]
                            if isinstance(unit, dict) and "Id" in unit:
                                max_id = max(max_id, unit["Id"])
                for value in data.values():
                    find_ids(value)
            elif isinstance(data, list):
                for item in data:
                    find_ids(item)
        
        find_ids(self.project_data)
        return max_id

    def _link_load_to_module(self, load_guid, module_name, canal):
        """Vincula um circuito de iluminação a um módulo"""
        try:
            modules_list = self.project_data['Areas'][0]['SubItems'][0]['AutomationBoards'][0]['ModulesList']
            for module in modules_list:
                if module['Name'] == module_name:
                    # tentar ON/OFF e depois DIM
                    for wanted in ('Load ON/OFF', 'Load Dim'):
                        for slot in module.get('Slots', []):
                            if slot.get('Name') == wanted:
                                while len(slot['SubItemsGuid']) < slot.get('SlotCapacity', 0):
                                    slot['SubItemsGuid'].append("00000000-0000-0000-0000-000000000000")
                                slot['SubItemsGuid'][canal-1] = load_guid
                                return True
                    break
        except Exception as e:
            print("Erro ao linkar load:", e)
        return False

    # Implementar métodos similares para:
    # _add_shade, _add_hvac, _link_shade_to_module, _link_hvac_to_module

    def export_project(self):
        """Exporta o projeto como JSON (formato Roehn Wizard)"""
        if not self.project_data:
            raise ValueError("Nenhum projeto para exportar")
            
        return json.dumps(self.project_data, indent=2, ensure_ascii=False)